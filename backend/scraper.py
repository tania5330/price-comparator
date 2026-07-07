import asyncio
import httpx
from bs4 import BeautifulSoup
import hashlib
import re
import json
import random
from datetime import datetime
from urllib.parse import urlparse, unquote


# Multiple User-Agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


# ─── Shared Helpers ─────────────────────────────────────────────────


def _generate_id(name: str, source: str) -> str:
    raw = f"{name}:{source}".encode()
    return hashlib.md5(raw).hexdigest()[:12]


def _parse_price(text: str) -> float | None:
    if not text:
        return None
    cleaned = re.sub(r"[^\d.,]", "", text)
    # Handle European format (1.234,56) vs US format (1,234.56)
    if "," in cleaned and "." in cleaned:
        if cleaned.rindex(",") > cleaned.rindex("."):
            # European: 1.234,56
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # US: 1,234.56
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # Could be thousands separator or decimal
        parts = cleaned.split(",")
        if len(parts[-1]) == 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    try:
        val = float(cleaned)
        return val if val > 0 else None
    except ValueError:
        return None


def _get_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


def _get_locale(location: str) -> tuple[str, str]:
    """Extract locale codes from location string."""
    gl, hl = "us", "en"
    location_lower = (location or "").lower()
    if "mexico" in location_lower or "méxico" in location_lower:
        gl, hl = "mx", "es"
    elif "colombia" in location_lower:
        gl, hl = "co", "es"
    elif "argentina" in location_lower:
        gl, hl = "ar", "es"
    elif "spain" in location_lower or "españa" in location_lower:
        gl, hl = "es", "es"
    elif "peru" in location_lower or "perú" in location_lower:
        gl, hl = "pe", "es"
    return gl, hl


def _extract_domain(url: str) -> str:
    """Extract clean domain name from URL for use as source name."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        domain = domain.replace("www.", "")
        # Capitalize the main domain name
        parts = domain.split(".")
        if len(parts) >= 2:
            return parts[-2].capitalize()
        return domain.capitalize() if domain else "Web"
    except Exception:
        return "Web"


def _extract_prices_from_text(text: str) -> list[float]:
    """Extract all price-like values from a text string."""
    if not text:
        return []
    patterns = [
        r"\$\s*([\d,]+\.?\d*)",                       # $199.99
        r"USD\s*([\d,]+\.?\d*)",                       # USD 199.99
        r"([\d,]+\.?\d*)\s*(?:USD|dollars?)",          # 199.99 USD
        r"€\s*([\d,]+\.?\d*)",                         # €199.99
        r"£\s*([\d,]+\.?\d*)",                         # £199.99
        r"S/\.?\s*([\d,]+\.?\d*)",                     # S/ 199.99
        r"MXN\s*([\d,]+\.?\d*)",                       # MXN 199.99
        r"(?:price|precio|costo)[:\s]*([\d,]+\.?\d{2})",  # price: 199.99
    ]
    prices = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            price = _parse_price(match.group(1))
            if price and 0.50 < price < 500_000:
                prices.append(price)
    return prices


# ─── Main Entry Point ───────────────────────────────────────────────


async def scrape_google_shopping(query: str, location: str = "United States") -> list[dict]:
    """Multi-source product search.

    Prioritizes reliable APIs (DummyJSON, FakeStoreAPI), then Google Shopping, then DuckDuckGo (as fallback).
    Returns merged and sorted results (products with prices first).
    """
    gl, hl = _get_locale(location)

    source_results = await asyncio.gather(
        _search_dummyjson(query),    # 1. Reliable API (first priority)
        _search_fakestore(query),    # 2. Reliable API (second priority)
        _scrape_google_shopping_page(query, gl, hl),  # 3. Google Shopping (best scraping source)
        _scrape_duckduckgo_products(query),  # 4. DuckDuckGo (fallback, lower quality)
        return_exceptions=True,
    )

    all_products: list[dict] = []
    source_names = ["DummyJSON", "FakeStore", "Google Shopping", "DuckDuckGo"]

    for i, result in enumerate(source_results):
        if isinstance(result, list):
            # Filter out low-quality results (no price, no link, or generic links)
            filtered_results = [
                p for p in result
                if p.get("price") is not None  # Must have price
                and p.get("product_link")      # Must have link
                and not (  # Skip obviously generic links
                    p.get("source_name") == "DuckDuckGo"
                    and (
                        "amazon.com" in p.get("product_link", "").lower()
                        and "/dp/" not in p.get("product_link", "").lower()
                        or "ebay.com" in p.get("product_link", "").lower()
                        and "/itm/" not in p.get("product_link", "").lower()
                    )
                )
            ]
            all_products.extend(filtered_results)
            print(f"[scraper] {source_names[i]}: {len(result)} total -> {len(filtered_results)} filtered")
        elif isinstance(result, Exception):
            print(f"[scraper] {source_names[i]} failed: {result}")

    # Sort: products with images first, then by price ascending
    all_products.sort(
        key=lambda p: (
            p.get("image") is None,  # Prioritize products with images
            p.get("price") is None or p.get("price") <= 0,  # Then with price
            p.get("price") or float("inf")  # Then by price
        )
    )

    print(f"[scraper] Total merged results: {len(all_products)}")
    return all_products[:200]


# ─── Source 4: DuckDuckGo (FALLBACK — real web results, lower quality) ───────


async def _scrape_duckduckgo_products(query: str) -> list[dict]:
    """Scrape DuckDuckGo HTML search for product results.

    DuckDuckGo's HTML endpoint is bot-friendly and returns real web results
    with product names, prices in snippets, and store URLs.
    """
    now = datetime.now().isoformat()
    results: list[dict] = []

    async with httpx.AsyncClient(
        headers=_get_headers(),
        follow_redirects=True,
        timeout=15.0,
    ) as client:
        try:
            # POST is more reliable than GET for DDG HTML endpoint
            response = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": f"{query} price buy", "b": ""},
            )
            # DDG returns 202 when rate-limiting — retry once after a short wait
            if response.status_code == 202:
                await asyncio.sleep(2)
                response = await client.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": f"{query} price buy", "b": ""},
                )
            if response.status_code >= 300:
                print(f"[DDG] HTTP {response.status_code}")
                return []
            # Read body INSIDE the context manager — connection closes after exit
            html = response.text
        except httpx.HTTPError as e:
            print(f"[DDG] Request failed: {e}")
            return []

    soup = BeautifulSoup(html, "html.parser")

    for result_el in soup.select(".result"):
        try:
            title_el = result_el.select_one(".result__a")
            snippet_el = result_el.select_one(".result__snippet")

            if not title_el:
                continue

            raw_name = title_el.get_text(strip=True)
            if not raw_name or len(raw_name) < 5:
                continue

            # Clean up title — remove trailing "- StoreName" or "| StoreName"
            name = re.sub(r"\s*[-|–—]\s*[A-Z][a-zA-Z0-9.& ]{2,30}\s*$", "", raw_name).strip()
            if len(name) < 5:
                name = raw_name

            # Extract real URL from DDG's redirect wrapper
            href = title_el.get("href", "")
            product_link = href
            if "uddg=" in href:
                match = re.search(r"uddg=([^&]+)", href)
                if match:
                    product_link = unquote(match.group(1))
            elif href.startswith("//"):
                product_link = f"https:{href}"

            source_name = _extract_domain(product_link)

            snippet = snippet_el.get_text(strip=True) if snippet_el else None

            # Try to find a price in snippet text
            price = None
            if snippet:
                prices = _extract_prices_from_text(snippet)
                if prices:
                    price = min(prices)  # lowest price mentioned

            # Also check title for prices
            if not price:
                prices = _extract_prices_from_text(raw_name)
                if prices:
                    price = min(prices)

            product_id = _generate_id(name, source_name)

            results.append({
                "id": product_id,
                "name": name,
                "canonical_name": name,
                "image": None,
                "description": snippet,
                "product_link": product_link,
                "source_name": source_name,
                "price": price,
                "old_price": None,
                "currency": "$",
                "price_raw": f"${price:.2f}" if price else None,
                "rating": None,
                "reviews_count": None,
                "delivery": None,
                "snippet": snippet,
                "scraped_at": now,
                "bestPrice": price,
                "availability": "unknown",
            })

        except Exception as e:
            print(f"[DDG] Parse error on one result: {e}")
            continue

    return results


# ─── Source 2: DummyJSON API (SECONDARY — always returns data) ──────


async def _search_dummyjson(query: str) -> list[dict]:
    """Search the free DummyJSON product API.

    Tries the full query first. Also checks if any word matches a known category
    to fetch category products directly.
    """
    now = datetime.now().isoformat()
    results: list[dict] = []
    
    category_mapping = {
        "perfume": "fragrances",
        "perfumes": "fragrances",
        "cologne": "fragrances",
        "fragrance": "fragrances",
        "fragrances": "fragrances",
        "groceries": "groceries",
        "food": "groceries",
        "grocery": "groceries",
        "laptop": "laptops",
        "laptops": "laptops",
        "notebook": "laptops",
        "phone": "smartphones",
        "phones": "smartphones",
        "smartphone": "smartphones",
        "smartphones": "smartphones",
        "mobile": "smartphones",
        "furniture": "furniture",
        "chair": "furniture",
        "table": "furniture",
        "sofa": "furniture",
        "dress": "womens-dresses",
        "dresses": "womens-dresses",
        "shirt": "mens-shirts",
        "shirts": "mens-shirts",
        "shoe": "mens-shoes",
        "shoes": "mens-shoes",
        "watch": "mens-watches",
        "watches": "mens-watches",
        "bag": "womens-bags",
        "bags": "womens-bags",
        "sunglasses": "sunglasses",
        "glasses": "sunglasses",
    }
    
    query_lower = query.lower()
    category_slug = None
    for w in query_lower.split():
        # Strip punctuation
        w_clean = re.sub(r"[^\w]", "", w)
        if w_clean in category_mapping:
            category_slug = category_mapping[w_clean]
            break

    urls_to_try = [
        ("search", f"https://dummyjson.com/products/search?q={query}&limit=50")
    ]
    if category_slug:
        urls_to_try.append(("category", f"https://dummyjson.com/products/category/{category_slug}?limit=50"))

    # Also try simplified keywords if query is multi-word
    words = [re.sub(r"[^\w]", "", w) for w in query_lower.split() if len(w) > 3]
    if len(words) >= 2:
        urls_to_try.append(("search_fallback", f"https://dummyjson.com/products/search?q={words[-1]}&limit=50"))

    all_products = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=10.0) as client:
        for tag, url in urls_to_try:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for p in data.get("products", []):
                        pid = p.get("id")
                        if pid not in seen_ids:
                            seen_ids.add(pid)
                            all_products.append(p)
            except Exception as e:
                print(f"[DummyJSON] Error fetching {url}: {e}")
                continue

    for product in all_products:
        try:
            name = product.get("title", "")
            if not name:
                continue

            price = product.get("price")
            discount_pct = product.get("discountPercentage", 0)
            old_price = None
            if price and discount_pct and discount_pct > 0:
                old_price = round(price / (1 - discount_pct / 100), 2)

            brand = product.get("brand", "")
            source_name = brand if brand else "Store"

            rating_val = product.get("rating")
            rating = round(float(rating_val), 1) if rating_val else None

            image = product.get("thumbnail")
            if not image:
                images = product.get("images", [])
                image = images[0] if images else None

            stock = product.get("stock", 0)
            product_id = _generate_id(name, source_name)

            results.append({
                "id": product_id,
                "name": name,
                "canonical_name": name,
                "image": image,
                "description": product.get("description"),
                "brand": brand,
                "category": product.get("category"),
                "product_link": f"https://dummyjson.com/products/{product.get('id', '')}",
                "source_name": source_name,
                "price": price,
                "old_price": old_price,
                "currency": "$",
                "price_raw": f"${price:.2f}" if price else None,
                "rating": rating,
                "reviews_count": len(product["reviews"]) if isinstance(product.get("reviews"), list) else None,
                "delivery": "Free shipping" if (price and price > 50) else None,
                "snippet": product.get("description"),
                "scraped_at": now,
                "bestPrice": price,
                "availability": "in_stock" if stock > 0 else "out_of_stock",
            })
        except Exception as e:
            print(f"[DummyJSON] Parse error: {e}")
            continue

    return results


# ─── Source 3: FakeStore API (TERTIARY — broad category coverage) ───


async def _search_fakestore(query: str) -> list[dict]:
    """Search the FakeStore API — a free public product API.

    Covers electronics, clothing, jewelry with real product names and images.
    Since FakeStore doesn't support keyword search, we fetch all products
    and filter locally. At least one significant keyword in the query
    must match the product title or category name.
    """
    now = datetime.now().isoformat()
    results: list[dict] = []
    
    # Extract clean query keywords (longer than 2 characters, or exact 'tv')
    query_words = set()
    for w in query.lower().split():
        w_clean = re.sub(r"[^\w]", "", w)
        if len(w_clean) >= 3 or w_clean in ["tv"]:
            query_words.add(w_clean)
            
    if not query_words:
        return []

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get("https://fakestoreapi.com/products?limit=100")
            if response.status_code != 200:
                print(f"[FakeStore] HTTP {response.status_code}")
                return []
            products = response.json()
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            print(f"[FakeStore] Error: {e}")
            return []

    # Map query words to specific product types or categories
    synonym_map = {
        "tv": ["monitor", "screen", "display", "tv", "television"],
        "television": ["monitor", "screen", "display", "tv", "television"],
        "laptop": ["laptop", "computer", "notebook"],
        "shoes": ["clothing", "wear"], # fake store doesn't have shoes, but clothing is closest
        "backpack": ["backpack", "foldsack", "bag"],
        "shirt": ["shirt", "t-shirt", "tshirt", "polo"],
        "jacket": ["jacket", "coat", "windbreaker"],
        "ring": ["ring", "jewelery", "jewelry"],
        "necklace": ["necklace", "jewelery", "jewelry"],
        "bracelet": ["bracelet", "jewelery", "jewelry"],
        "earring": ["earring", "jewelery", "jewelry"],
    }

    for product in products:
        try:
            name = product.get("title", "")
            category = (product.get("category") or "").lower()
            description = (product.get("description") or "").lower()
            
            name_words = set(re.findall(r"\w+", name.lower()))
            category_words = set(re.findall(r"\w+", category.lower()))
            
            # Check for direct keyword matches in product title
            title_match = False
            for qw in query_words:
                if qw in name_words or any(qw in nw for nw in name_words):
                    title_match = True
                    break
                    
            # Check for synonym/conceptual matches
            synonym_match = False
            for qw in query_words:
                if qw in synonym_map:
                    synonyms = synonym_map[qw]
                    # If any synonym is in the title words
                    if any(syn in name_words for syn in synonyms):
                        synonym_match = True
                        break

            # Also allow general category queries like "electronics", "jewelry", "jewelery", "clothing", "clothes"
            category_match = False
            for qw in query_words:
                if qw in ["electronics", "jewelry", "jewelery", "clothing", "clothes"]:
                    if qw in category_words or any(qw in cw for cw in category_words):
                        category_match = True
                        break
                    if qw == "clothing" and "clothing" in category:
                        category_match = True
                        break

            # If no match, skip this product
            if not (title_match or synonym_match or category_match):
                continue

            price = product.get("price")
            rating_data = product.get("rating", {})
            rating = round(float(rating_data.get("rate", 0)), 1) if rating_data else None
            reviews_count = rating_data.get("count") if rating_data else None

            product_id = _generate_id(name, "FakeStore")

            results.append({
                "id": product_id,
                "name": name,
                "canonical_name": name,
                "image": product.get("image"),
                "description": product.get("description"),
                "category": category,
                "product_link": f"https://fakestoreapi.com/products/{product.get('id', '')}",
                "source_name": "FakeStore",
                "price": price,
                "old_price": None,
                "currency": "$",
                "price_raw": f"${price:.2f}" if price else None,
                "rating": rating if rating and rating > 0 else None,
                "reviews_count": reviews_count,
                "delivery": "Free shipping" if price and price > 35 else None,
                "snippet": product.get("description", "")[:150],
                "scraped_at": now,
                "bestPrice": price,
                "availability": "in_stock",
            })
        except Exception as e:
            print(f"[FakeStore] Parse error: {e}")
            continue

    return results


# ─── Source 4: Google Shopping (QUATERNARY — may be blocked) ────────

async def _scrape_google_shopping_page(query: str, gl: str, hl: str) -> list[dict]:
    """Try to scrape Google Shopping results.

    This source MAY fail because Google actively blocks non-browser
    requests. It is kept as a bonus source — when it works, the data
    is high quality. When it fails, the other sources cover the gap.
    """
    params = {
        "q": query,
        "tbm": "shop",
        "hl": hl,
        "gl": gl,
        "num": "30",
    }

    results: list[dict] = []
    now = datetime.now().isoformat()

    async with httpx.AsyncClient(
        headers=_get_headers(),
        follow_redirects=True,
        timeout=15.0,
    ) as client:
        try:
            response = await client.get(
                "https://www.google.com/search", params=params
            )
            if response.status_code != 200:
                print(f"[Google] HTTP {response.status_code}")
                return []
            html = response.text
        except httpx.HTTPError as e:
            print(f"[Google] Request failed: {e}")
            return []

    soup = BeautifulSoup(html, "html.parser")

    # Try multiple CSS selectors — Google changes class names frequently
    selectors = [
        ".sh-dgr__content",
        ".sh-dlr__list-result",
        "[data-docid]",
        ".sh-pr__product-result",
        ".KZmu8e",
        ".i0X6df",
        ".xcR77",
        ".mnr-c",
    ]

    product_cards = []
    for selector in selectors:
        cards = soup.select(selector)
        if cards:
            product_cards = cards
            break

    for card in product_cards:
        product = _extract_product_from_card(card, now)
        if product:
            results.append(product)

    # Fallback: check for JSON-LD structured data
    if not results:
        for script in soup.select("script[type='application/ld+json']"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "Product":
                    product = _extract_from_jsonld(data, now)
                    if product:
                        results.append(product)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            product = _extract_from_jsonld(item, now)
                            if product:
                                results.append(product)
            except (json.JSONDecodeError, TypeError):
                continue

    return results


# ─── Google Shopping Card Parsers ────────────────────────────────────


def _extract_product_from_card(card, now: str) -> dict | None:
    """Extract product data from a Google Shopping card element."""
    try:
        # Name
        name_el = (
            card.select_one("h3")
            or card.select_one("h4")
            or card.select_one("[role='heading']")
            or card.select_one(".tAxDx")
            or card.select_one(".EI11Pd")
            or card.select_one(".Xjkr3b")
            or card.select_one("a[class*='shntl']")
        )
        name = name_el.get_text(strip=True) if name_el else None
        if not name or len(name) < 3:
            return None

        # Price
        price_el = (
            card.select_one(".a8Pemb")
            or card.select_one(".HRLxBb")
            or card.select_one(".kHxwFf")
            or card.select_one("[data-price]")
            or card.select_one("span[aria-label*='price']")
        )
        price_text = price_el.get_text(strip=True) if price_el else None
        if not price_text and price_el:
            price_text = price_el.get("data-price")
        price = _parse_price(price_text)

        # Image
        img_el = card.select_one("img[src]:not([src^='data:'])")
        if not img_el:
            img_el = card.select_one("img[data-src]")
        image = None
        if img_el:
            image = img_el.get("src") or img_el.get("data-src")
            if image and image.startswith("data:"):
                image = None

        # Source/store
        source_el = (
            card.select_one(".aULzUe")
            or card.select_one(".IuHnof")
            or card.select_one(".E5ocAb")
            or card.select_one(".shntl")
            or card.select_one(".LbUacb")
        )
        source_name = source_el.get_text(strip=True) if source_el else "Google Shopping"

        # Link
        product_link = None
        link_el = (
            card.select_one("a[href*='url=']")
            or card.select_one("a[href^='http']")
            or card.select_one("a[href]")
        )
        if link_el:
            href = link_el.get("href", "")
            if "/url?" in href:
                match = re.search(r"[?&](?:url|q)=([^&]+)", href)
                product_link = match.group(1) if match else href
            elif href.startswith("http"):
                product_link = href
            elif href.startswith("/"):
                product_link = f"https://www.google.com{href}"

        # Rating
        rating = None
        rating_el = (
            card.select_one("[aria-label*='out of']")
            or card.select_one("[aria-label*='rating']")
            or card.select_one(".Rsc7Yb")
        )
        if rating_el:
            label = rating_el.get("aria-label", "") or rating_el.get_text(strip=True)
            match = re.search(r"(\d+\.?\d*)", label)
            if match:
                rating = float(match.group(1))
                if rating > 5:
                    rating = None

        # Reviews
        reviews_count = None
        reviews_el = card.select_one(".qIiRFd") or card.select_one(".NMm5M")
        if reviews_el:
            rev_text = reviews_el.get_text(strip=True)
            rev_match = re.search(r"(\d[\d,]*)", rev_text)
            if rev_match:
                reviews_count = int(rev_match.group(1).replace(",", ""))

        # Delivery
        delivery_el = (
            card.select_one(".vEjMR")
            or card.select_one(".dD8iuc")
            or card.select_one(".SzGJMe")
        )
        delivery = delivery_el.get_text(strip=True) if delivery_el else None

        # Old price
        old_price_el = (
            card.select_one(".Bk4TYd")
            or card.select_one(".AdWm1c")
            or card.select_one("s")
        )
        old_price = _parse_price(old_price_el.get_text(strip=True)) if old_price_el else None

        # Snippet
        snippet_el = card.select_one(".hBUZL") or card.select_one(".translate-content")
        snippet = snippet_el.get_text(strip=True) if snippet_el else None

        product_id = _generate_id(name, source_name)

        return {
            "id": product_id,
            "name": name,
            "canonical_name": name,
            "image": image,
            "description": snippet,
            "product_link": product_link,
            "source_name": source_name,
            "price": price,
            "old_price": old_price,
            "currency": "$",
            "price_raw": price_text,
            "rating": rating,
            "reviews_count": reviews_count,
            "delivery": delivery,
            "snippet": snippet,
            "scraped_at": now,
            "bestPrice": price,
            "availability": "in_stock" if delivery else "unknown",
        }

    except Exception as e:
        print(f"[Google] Card parse error: {e}")
        return None


def _extract_from_jsonld(data: dict, now: str) -> dict | None:
    """Extract product info from JSON-LD structured data."""
    try:
        name = data.get("name")
        if not name:
            return None

        price = None
        currency = "$"
        offers = data.get("offers", {})
        if isinstance(offers, dict):
            price = _parse_price(str(offers.get("price", "")))
            currency = offers.get("priceCurrency", "$")
        elif isinstance(offers, list) and offers:
            price = _parse_price(str(offers[0].get("price", "")))
            currency = offers[0].get("priceCurrency", "$")

        image = data.get("image")
        if isinstance(image, list):
            image = image[0] if image else None

        brand_data = data.get("brand", {})
        brand = brand_data.get("name") if isinstance(brand_data, dict) else None

        source_name = "Google Shopping"
        product_id = _generate_id(name, source_name)

        return {
            "id": product_id,
            "name": name,
            "canonical_name": name,
            "image": image,
            "description": data.get("description"),
            "brand": brand,
            "product_link": data.get("url"),
            "source_name": source_name,
            "price": price,
            "old_price": None,
            "currency": currency,
            "price_raw": str(price) if price else None,
            "rating": None,
            "reviews_count": None,
            "delivery": None,
            "snippet": data.get("description"),
            "scraped_at": now,
            "bestPrice": price,
            "availability": "unknown",
        }
    except Exception:
        return None
