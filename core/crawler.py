import requests
import urllib3
from bs4 import BeautifulSoup
from .utils import normalize_url, same_domain, valid_url

urllib3.disable_warnings()

session = requests.Session()

VERBOSE = False

HEADERS_PC = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

HEADERS_MOBILE = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
}

def fetch(url, headers):
    try:
        r = session.get(url, headers=headers, timeout=2, verify=False)
        if r.status_code != 200:
            return ""
        ct = r.headers.get("Content-Type", "").lower()
        if any(x in ct for x in ["image/", "audio/", "video/", "font/", "application/pdf", "zip", "rar"]):
            return ""
        if len(r.content) > 2000000:
            if VERBOSE:
                print(f"内容过大: {len(r.content)} bytes - {url}")
            return r.text[:2000000]
        return r.text
    except requests.exceptions.RequestException as e:
        # 只在 VERBOSE 模式下显示错误
        if VERBOSE:
            print(f"请求异常 {url}: {str(e)}")
        return ""
    except Exception as e:
        # 只在 VERBOSE 模式下显示错误
        if VERBOSE:
            print(f"其他异常 {url}: {str(e)}")
        return ""


def extract_links(html, base):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.find_all(["a", "link", "iframe"]):
        href = tag.get("href") or tag.get("src")
        if not href:
            continue
        if not valid_url(href):
            continue
        u = normalize_url(href, base)
        if not same_domain(u, base):
            continue
        links.append(u)
    return list(set(links))


def get_sitemap(base):
    urls = []
    try:
        xml = fetch(base.rstrip("/") + "/sitemap.xml", HEADERS_PC)
        if not xml:
            return urls
        soup = BeautifulSoup(xml, "xml")
        for loc in soup.find_all("loc"):
            loc_text = loc.text.strip()
            if loc_text:
                urls.append(loc_text)
    except Exception as e:
        print(f"sitemap parse error: {e}")
        pass
    return urls


def get_robots(base):
    urls = []
    try:
        txt = fetch(base.rstrip("/") + "/robots.txt", HEADERS_PC)
        if not txt:
            return urls
        for line in txt.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith(("allow:", "disallow:")):
                parts = line.split(":", 1)
                if len(parts) < 2:
                    continue
                path = parts[1].strip()
                if path and path.startswith("/"):
                    full_url = base.rstrip("/") + path
                    urls.append(full_url)
    except Exception as e:
        print(f"robots parse error: {e}")
        pass
    return urls


def get_discovered_urls(base):
    """尝试从 sitemap.xml 和 robots.txt 获取额外可爬页面"""
    urls = set()
    urls.update(get_sitemap(base))
    urls.update(get_robots(base))
    return list(urls)