import re

# 内容关键词（赌博、色情等敏感词）
KEYWORD_REGEX = re.compile(
    r"博彩|赌场|真人荷官|下注|体育投注|百家乐"
    r"|成人直播|裸聊|约炮|色情|梯子|翻墙|赌球"
    r"|极速提现|棋牌|六合彩|老虎机|皇冠"
    r"|福布斯公司|福布斯|开户|上分|下分|微信同步|开户上分|/tz\.js"
    ,re.I
)

# JS 代码特征（动态劫持、iframe 注入等）
JS_PATTERN = re.compile(
    # 动态创建 iframe + 全屏样式（更宽松，允许任意字符间隔）
    r"createElement\s*\(\s*['\"]iframe['\"]\s*\).*?width\s*:\s*100%\s*;?\s*height\s*:\s*100%|"
    # document.write 写入 viewport（更宽松）
    r"document\.write\s*\([^)]*viewport[^)]*width\s*=\s*device-width|"
    # 固定定位全屏覆盖（支持分号或空格分隔）
    r"position\s*:\s*fixed[^}]*top\s*:\s*0[^}]*bottom\s*:\s*0|"
    # document.write 输出 outerHTML（支持任意变量名）
    r"document\.write\s*\(\s*[a-zA-Z_]\w*\.outerHTML\s*\)"
    ,re.I | re.S
)

HIDDEN_PATTERN = re.compile(
    r"display\s*:\s*none|"
    r"visibility\s*:\s*hidden|"
    r"opacity\s*:\s*0|"
    r"font-size\s*:\s*0|"
    r"height\s*:\s*0|"
    r"width\s*:\s*0|"
    r"text-indent\s*:\s*-?\d+px|"
    r"left\s*:\s*-?\d+px",
    re.I
)

BASE64_PATTERN = re.compile(
    r"[A-Za-z0-9+/]{30,}={0,2}"
)

CHARCODE_PATTERN = re.compile(
    r"String\.fromCharCode\((.*?)\)"
)

META_REFRESH = re.compile(
    r"http-equiv\s*=\s*[\"']?refresh",
    re.I
)