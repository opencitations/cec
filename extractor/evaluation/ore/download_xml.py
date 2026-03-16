"""
fast_download.py
- Concurrent downloader using asyncio + aiohttp
- Usage: python fast_download.py
"""
import asyncio
import aiohttp
from aiohttp import ClientConnectorError, ClientResponseError
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse



MAX_RETRIES = 3
RETRY_DELAY = 2.0

async def fetch_listing(session, url):
    async with session.get(url, raise_for_status=True) as resp:
        return await resp.text()

def extract_xml_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base_url, href)
        if "/articles/" in full and full.endswith("/xml"):
            links.append(full)
    seen = set()
    out = []
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

def filename_from_url(url, out_dir):
    p = urlparse(url).path.strip("/")
    fn = p.replace("/", "_") + ".xml"
    return os.path.join(out_dir, fn)

async def download_one(session, sem, url, out_dir):
    dest = filename_from_url(url, out_dir)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return url, True, "exists"

    for attempt in range(1, MAX_RETRIES+1):
        try:
            async with sem:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    content = await resp.read()
                    with open(dest, "wb") as f:
                        f.write(content)
            return url, True, "downloaded"
        except (ClientConnectorError, ClientResponseError, asyncio.TimeoutError) as e:
            reason = str(e)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)
            else:
                return url, False, reason
        except Exception as e:
            return url, False, str(e)

async def main(concurrency, listing_url, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    conn = aiohttp.TCPConnector(limit_per_host=concurrency)
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        html = await fetch_listing(session, listing_url)
        links = extract_xml_links(html, listing_url)
        print(f"Found {len(links)} xml links.")

        sem = asyncio.Semaphore(concurrency)
        tasks = [download_one(session, sem, url, out_dir) for url in links]
        done = await asyncio.gather(*tasks)
        for url, ok, msg in done:
            status = "OK" if ok else "FAILED"
            print(f"{status}: {url} -> {msg}")

