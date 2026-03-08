import argparse
import signal
import warnings
import urllib3
import time  # 用于重试延迟（可选）

from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import XMLParsedAsHTMLWarning

from core import crawler, detector

urllib3.disable_warnings()
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

STOP_SCAN = False
VERBOSE = False  # 默认关闭详细输出


def signal_handler(sig, frame):
    global STOP_SCAN
    print("\n[!] Ctrl+C detected, stopping scan...")
    STOP_SCAN = True


signal.signal(signal.SIGINT, signal_handler)


# -------------------------
# 单页面扫描 - 双 UA 版本
# -------------------------
def scan_page(url):
    if VERBOSE:
        print(f" [SCAN_PAGE] 开始处理: {url}")

    html_pc = crawler.fetch(url, crawler.HEADERS_PC)
    
    # 如果 PC 请求失败（超时或空内容），直接返回失败标记
    if not html_pc:
        if VERBOSE:
            print(f" [SKIP] {url} PC请求失败，跳过该URL")
        return "FETCH_FAILED", None, None
    
    # PC 成功后再请求 Mobile
    html_mobile = crawler.fetch(url, crawler.HEADERS_MOBILE)

    if VERBOSE:
        print(f" [SCAN_PAGE] {url} - PC len: {len(html_pc or '')}, Mobile len: {len(html_mobile or '')}")

    # PC 检测
    pc_score, pc_findings, pc_keyword_hit = detector.detect(url, html_pc)

    # Mobile 检测
    mobile_score, mobile_findings, mobile_keyword_hit = 0, [], False
    if html_mobile:
        mobile_score, mobile_findings, mobile_keyword_hit = detector.detect(url, html_mobile)

    # UA 差异加分
    if html_mobile and html_pc != html_mobile:
        pc_score += 5
        pc_findings.append(("Mobile UA差异", "PC与Mobile返回不同"))
        mobile_score += 5
        mobile_findings.append(("Mobile UA差异", "PC与Mobile返回不同"))

    # PC 异常短 → fallback 到 Mobile
    if len(html_pc) < 500 and html_mobile and len(html_mobile) > 1000:
        if VERBOSE:
            print(f"  [FALLBACK] PC 内容异常短 ({len(html_pc)})，使用 Mobile 结果")
        pc_score = mobile_score
        pc_findings = mobile_findings
        html_pc = html_mobile  # 用于提取链接

    return (
        (url, pc_score, pc_findings, mobile_score, mobile_findings),
        html_pc,
        html_mobile
    )


# -------------------------
# 整站扫描
# -------------------------
def scan_site(url, max_pages=30):
    visited = set()
    queue = []

    # 第一步：强制扫描主页面
    print(f" -> 先扫描主页面: {url}")
    visited.add(url)
    queue.append(url)

    main_result, main_html, main_mobile_html = scan_page(url)

    # 如果主页面获取失败，直接跳过整个站点
    if main_result == "FETCH_FAILED":
        print(f" [!] {url} 主页面请求失败，跳过该站点")
        return None

    results = []

    if main_result:
        page_url, pc_score, pc_findings, mob_score, mob_findings = main_result
        if pc_score >= 4 or mob_score >= 4:
            print(f"\033[91m[RISK] {page_url}   PC: {pc_score} | Mobile: {mob_score}\033[0m")
            results.append(main_result)

    # 提取链接
    main_content = main_html if main_html else main_mobile_html
    if main_content:
        links = crawler.extract_links(main_content, url)
        if VERBOSE:
            print(f" [EXTRACT] 从主页面提取到 {len(links)} 个链接")
        for l in links:
            if l not in visited:
                queue.append(l)
                visited.add(l)
    else:
        if VERBOSE:
            print(f" [WARN] 主页面内容为空，仍继续尝试其他入口")

    # 第二步：sitemap 和 robots
    extra_urls = crawler.get_discovered_urls(url)
    print(f"  [发现额外入口: {len(extra_urls)} 个]")
    queue.extend([eu for eu in extra_urls if eu not in visited])
    queue = list(set(queue))

    # 多线程批量扫描
    with ThreadPoolExecutor(max_workers=10) as executor:
        while queue and len(visited) < max_pages:
            if STOP_SCAN:
                break

            batch = []
            while queue and len(batch) < 10:
                u = queue.pop(0)
                if u in visited:
                    continue
                visited.add(u)
                print(f" -> scanning {u}")  # 保留这个
                batch.append(u)

            futures = [executor.submit(scan_page, u) for u in batch]
            html_dict = {}

            for f in as_completed(futures):
                page_result = f.result()
                
                # 跳过获取失败的页面
                if page_result == "FETCH_FAILED":
                    continue
                    
                if not page_result:
                    continue

                try:
                    page_info, html_pc, html_mobile = page_result
                    if not page_info:
                        continue

                    url_in_result = page_info[0]
                    html_dict[url_in_result] = html_pc

                    pc_score = page_info[1]
                    mob_score = page_info[3]

                    if pc_score >= 4 or mob_score >= 4:
                        print(f"\033[91m[RISK] {url_in_result}   PC: {pc_score} | Mobile: {mob_score}\033[0m")
                        results.append(page_info)
                except Exception as e:
                    if VERBOSE:
                        print(f"  [ERROR] 处理页面时出错: {str(e)}")
                    continue

            # 提取链接
            for u in batch:
                html = html_dict.get(u, "")
                if not html:
                    continue
                links = crawler.extract_links(html, u)
                for l in links:
                    if l.startswith(url) and l not in visited:
                        queue.append(l)
                        visited.add(l)

    return results


# -------------------------
# 主程序
# -------------------------
def main():
    global VERBOSE

    parser = argparse.ArgumentParser(description="暗链扫描工具")
    parser.add_argument("-i", required=True, help="输入目标文件")
    parser.add_argument("-o", required=True, help="输出报告文件")
    parser.add_argument("-x", "--proxy", help="代理地址，例如 http://127.0.0.1:8080")
    parser.add_argument("-I", "--info", action="store_true", help="启用详细输出模式（显示所有扫描页面处理信息）")

    args = parser.parse_args()

    VERBOSE = args.info

    if args.proxy:
        proxies = {
            "http": args.proxy,
            "https": args.proxy,
        }
        crawler.session.proxies.update(proxies)
        print(f"[*] 使用代理: {args.proxy}")
    else:
        print("[*] 未指定代理，直接请求")

    targets = open(args.i).read().splitlines()
    report = "# 暗链扫描报告\n\n"

    for t in targets:
        if STOP_SCAN:
            break
        print("Scanning", t)
        res = scan_site(t)
        
        # 处理跳过的情况
        if res is None:
            report += f"## {t}\n\n"
            report += "站点请求失败，已跳过\n\n"
            continue
            
        report += f"## {t}\n\n"
        if not res:
            report += "未发现暗链\n\n"
            continue

        for page_info in res:
            url, pc_score, pc_findings, mob_score, mob_findings = page_info
            report += f"### 页面 {url}\n\n"
            report += f"**PC 版本** 风险评分: {pc_score}\n"
            for f in pc_findings:
                report += f"- {f[0]}\n```\n{str(f[1])[:400]}\n```\n\n"
            report += f"**Mobile 版本** 风险评分: {mob_score}\n"
            for f in mob_findings:
                report += f"- {f[0]}\n```\n{str(f[1])[:400]}\n```\n\n"
            report += "---\n\n"

    open(args.o, "w", encoding="utf8").write(report)
    print("\n[+] Scan finished")
    print(f"[+] Report saved: {args.o}")


if __name__ == "__main__":
    main()