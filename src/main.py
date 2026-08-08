import asyncio
import json
import logging
import random
import re
import sys
from datetime import datetime, timezone
from urllib.parse import quote

import httpx

try:
    from apify import Actor
except Exception:
    Actor = None

BASE_URL = "https://www.jackroad.co.jp"
SEARCH_PATH = "/shop/goods/search.aspx"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.8",
}

PRODUCT_ANCHOR_RE = re.compile(
    r'<a[^>]*href="/shop/g/g([A-Za-z0-9]+)/"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def build_search_url(keyword: str, classification: int, page: int) -> str:
    params = {
        "classification": str(classification),
        "p": str(page),
        "ps": "30",
        "sort": "ard-gn-ic1d-gd",
        "search": quote(keyword, safe=""),
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{BASE_URL}{SEARCH_PATH}?{qs}"


def parse_product_list(html: str, keyword: str = "") -> list[dict]:
    matches = list(PRODUCT_ANCHOR_RE.finditer(html))
    if not matches:
        return []

    parsed_items = []
    for m in matches:
        pid = m.group(1)
        text = strip_html(m.group(2))
        parsed_items.append({"pos": m.start(), "pid": pid, "text": text})

    products = []
    seen = set()
    for item in parsed_items:
        if item["pid"] in seen:
            continue
        seen.add(item["pid"])
        products.append({"pid": item["pid"], "start": item["pos"], "title": "", "end": len(html)})

    known_brands = [
        "ROLEX", "ロレックス",
        "OMEGA", "オメガ",
        "TUDOR", "チューダー", "チュードル",
        "CARTIER", "カルティエ",
        "PANERAI", "パネライ",
        "IWC",
        "SEIKO", "セイコー",
        "GRAND SEIKO", "グランドセイコー",
        "CITIZEN", "シチズン",
        "AUDEMARS", "オーデマピゲ", "オーデマ ピゲ",
        "PATEK", "パテック",
    ]

    for i, prod in enumerate(products):
        if i + 1 < len(products):
            prod["end"] = products[i + 1]["start"]
        block = html[prod["start"]:prod["end"]]

        for item in parsed_items:
            if item["pid"] == prod["pid"] and item["text"]:
                prod["title"] = item["text"]
                break

        title = re.sub(r"\s+", " ", prod["title"]).strip()

        price_matches = re.findall(r"￥\s*([0-9,]+)\s*（税込）", block)
        if price_matches:
            price_str = price_matches[-1]
        else:
            m_list = re.findall(r"￥\s*([0-9,]+)", block)
            price_str = m_list[-1] if m_list else None

        price = None
        if price_str:
            digits = re.sub(r"\D", "", price_str)
            try:
                price = int(digits)
            except ValueError:
                price = None

        normalized = re.sub(r"\s+", "", block)
        condition = None
        for cond in ["ヴィンテージ", "中古", "新品", "未使用"]:
            if cond in normalized:
                condition = cond
                break

        stock_match = re.search(r"在庫あり|在庫なし|商談中|売約済|お取り寄せ", block)
        stock = stock_match.group(0) if stock_match else None

        img_match = re.search(r'<img[^>]+(?:data-src|src)="([^"]+)"', block)
        image = img_match.group(1) if img_match else None
        if image:
            if image.startswith("//"):
                image = "https:" + image
            elif image.startswith("/"):
                image = f"{BASE_URL}{image}"

        norm_title = title.upper()
        brand = None
        for b in sorted(known_brands, key=len, reverse=True):
            if norm_title.startswith(b.upper()):
                brand = b
                break
        if brand is None:
            brand = keyword if keyword else None

        products[i] = {
            "productId": prod["pid"],
            "title": title,
            "price": price,
            "brand": brand,
            "condition": condition,
            "stockStatus": stock,
            "productUrl": f"{BASE_URL}/shop/g/g{prod['pid']}/",
            "imageUrl": image,
        }

    return products


async def fetch_html(client: httpx.AsyncClient, url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code == 200:
                return resp.text
            logging.warning("GET %s -> %s", url, resp.status_code)
        except Exception as exc:
            logging.warning("Fetch error (%s): %s", url, exc)
        await asyncio.sleep(2 ** attempt + random.random())
    raise RuntimeError(f"Failed to fetch: {url}")


async def get_actor_input():
    if Actor and getattr(Actor, "is_at_home", False):
        actor_input = await Actor.get_input() or {}
    else:
        raw = sys.stdin.read()
        actor_input = json.loads(raw) if raw.strip() else {}
    return actor_input


async def push_data(item: dict) -> None:
    if Actor and getattr(Actor, "is_at_home", False):
        await Actor.push_data(item)
    else:
        print(json.dumps(item, ensure_ascii=False))


async def amain() -> None:
    if Actor and getattr(Actor, "is_at_home", False):
        await Actor.init()

    try:
        actor_input = await get_actor_input()

        keyword = actor_input.get("keyword") or ""
        if not keyword:
            raise ValueError("keyword is required")

        classification = int(actor_input.get("classification", 2))
        max_items = int(actor_input.get("maxItems", 100))
        max_items = max(1, min(max_items, 500))

        proxy_url = None
        if Actor and getattr(Actor, "is_at_home", False):
            proxy_config = await Actor.create_proxy_configuration(actor_input=actor_input)
            if proxy_config:
                proxy_url = await proxy_config.new_url()

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            proxy=proxy_url,
        ) as client:
            collected = 0
            page = 1

            while collected < max_items:
                url = build_search_url(keyword, classification, page)
                html = await fetch_html(client, url)
                products = parse_product_list(html, keyword)

                if not products:
                    break

                for product in products:
                    product["scrapedAt"] = datetime.now(timezone.utc).isoformat()
                    await push_data(product)
                    collected += 1
                    if collected >= max_items:
                        break

                if len(products) < 30:
                    break

                page += 1
                await asyncio.sleep(random.uniform(1.0, 3.0))

    finally:
        if Actor and getattr(Actor, "is_at_home", False):
            await Actor.exit()


def main() -> None:
    asyncio.run(amain())
