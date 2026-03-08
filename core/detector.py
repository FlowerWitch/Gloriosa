from bs4 import BeautifulSoup
import rules.rules as rules
from core.decoder import decode_base64, decode_charcode
from core.utils import is_external


def detect(url, html):
    score = 0
    findings = []
    keyword_hit = False

    # -------------------------
    # 关键词顶格检测
    # -------------------------
    m = rules.KEYWORD_REGEX.search(html)
    if m:
        score += 15
        keyword_hit = True
        findings.append(("🚨关键词命中 (html)", m.group()))

    # 新增：meta title / description / keywords 检测（常见藏暗链的地方）
    soup = BeautifulSoup(html, "html.parser")  # 移到这里，确保 soup 已定义
    title = soup.title.string if soup.title else ""
    if title and rules.KEYWORD_REGEX.search(title):
        score += 8
        findings.append(("标题含关键词", title.strip()[:200]))

    for meta in soup.find_all("meta", attrs={"name": ["description", "keywords"]}):
        content = meta.get("content", "")
        if content and rules.KEYWORD_REGEX.search(content):
            score += 8
            findings.append(("Meta 含关键词", content[:200]))

    # -------------------------
    # 隐藏外链
    # -------------------------

    for a in soup.find_all("a"):
        tag = str(a)
        href = a.get("href")
        if not href:
            continue
        if rules.HIDDEN_PATTERN.search(tag):
            if is_external(href, url):
                score += 4
                findings.append(("隐藏外链", tag))
        if rules.KEYWORD_REGEX.search(tag) and is_external(href, url):
            score += 5
            findings.append(("关键词外链", tag))

    # -------------------------
    # iframe
    # -------------------------

    for iframe in soup.find_all("iframe"):
        src = iframe.get("src")
        if src and is_external(src, url):
            score += 4
            findings.append(("iframe外链", str(iframe)))

    # -------------------------
    # meta refresh
    # -------------------------

    if rules.META_REFRESH.search(html):
        score += 3
        findings.append(("meta refresh", html[:200]))

    # -------------------------
    # JS 检测
    # -------------------------

    for script in soup.find_all("script"):
        js = script.text
        if not js:
            continue
        decoded = decode_base64(js)
        for d in decoded:
            if "http" in d:
                score += 3
                findings.append(("Base64URL", d))
        decoded2 = decode_charcode(js)
        for d in decoded2:
            if "http" in d:
                score += 3
                findings.append(("CharCodeURL", d))

    return score, findings, keyword_hit