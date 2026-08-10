# Jackroad Used Luxury Watch Scraper

**Scrape pre-owned Rolex, Omega, Cartier and more from one of Japan's largest watch dealers – Jackroad. Ideal for price monitoring, reseller arbitrage, and market research.**

> 💡 **For cross-shop comparison**, use the [Japan Watch Market Scraper](https://apify.com/fruitful_quintessence/japan-watch-market-scraper) — it compares Jackroad against Kitamura used watches in a single dataset.

## Output Sample

    {"productId": "ABC123", "title": "Rolex Submariner", "price": "1,234,000", "brand": null, "condition": "中古", "stockStatus": "在庫あり", "productUrl": "https://www.jackroad.co.jp/shop/g/gABC123/", "imageUrl": "https://example.com/img.jpg", "scrapedAt": "2024-05-01T12:00:00.000Z"}

    {"productId": "DEF456", "title": "OMEGA Speedmaster", "price": "850,000", "brand": null, "condition": "ヴィンテージ", "stockStatus": "商談中", "productUrl": "https://www.jackroad.co.jp/shop/g/gDEF456/", "imageUrl": null, "scrapedAt": "2024-05-01T12:05:00.000Z"}

## Input

- `keyword` (string, required): Brand name or keyword to search. Examples: `ROLEX`, `OMEGA`, `カルティエ`
- `classification` (string, optional): `"0"` for new items (新品), `"2"` for used/vintage (中古/ヴィンテージ). Default: `"2"`
- `maxItems` (integer, optional): Maximum number of products to scrape (1–500). Default: `100`
- `proxyConfiguration` (object, optional): Apify proxy configuration for reliable scraping

## Use Cases

- **Rolex price monitoring** – Track daily price changes for used Rolex models.
- **Japan used luxury watch arbitrage** – Identify underpriced vintage watches for resale.
- **Vintage watch inventory tracking** – Keep an eye on stock status and availability of hard‑to‑find pieces.

## Integrations

- **Apify + Google Sheets** – Export scraped data to a Google Sheet for live price analysis.
- **Apify + Slack** – Send alerts when a specific watch drops below your target price.
- **Apify + Postgres** – Store historical price data for long‑term market research.

## Pricing

This actor runs on Apify’s **pay‑per‑use** model. You are charged based on compute units consumed. Visit [Apify Pricing](https://apify.com/pricing) for details.

## Limitations

- Only listing page data is extracted. Product detail pages are **not** fetched.
- The parser relies on the current HTML structure of Jackroad. If the site changes its markup, the actor may require updates.
- Product condition detection is basic and may not capture all possible variants.

## FAQ

### Can I scrape Rolex prices?

Yes. Enter `ROLEX` as the `keyword`, adjust `maxItems`, and run the actor. Prices are collected from the listing pages.

### Is this allowed?

The actor is designed for personal research and price monitoring. Always respect the target website's terms of service and robot.txt. Use official APIs where available.

### Can I get individual watch specifications like movement or serial number?

Not with this actor. It only extracts what is visible on the search result listing. For detailed specifications, consider an additional detail‑page scraper.

## Changelog

- **v0.0.1** – Initial release
  - Scrape Jackroad search result listings
  - Extract product ID, title, price, condition, stock status, URL, image URL, and timestamp
  - Supports keyword search, classification filter, and max items limit
  - Optional proxy support via Apify proxy configuration
