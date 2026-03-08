import tldextract
from urllib.parse import urljoin

BAD_EXT = (
".jpg",".png",".gif",".svg",".pdf",".zip",".rar",".7z",
".mp4",".mp3",".avi",".css",".woff",".ttf",".ico"
)

def is_external(url, base):

    d1 = tldextract.extract(url)
    d2 = tldextract.extract(base)

    return d1.domain != d2.domain


def normalize_url(url, base):

    return urljoin(base, url)


def same_domain(url, base):

    d1 = tldextract.extract(url)
    d2 = tldextract.extract(base)

    return d1.domain == d2.domain


def valid_url(url):

    if url.startswith(("javascript","mailto","#")):
        return False

    for ext in BAD_EXT:

        if url.lower().endswith(ext):
            return False

    return True