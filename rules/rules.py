# rules.py 完整替换
import re

KEYWORD_REGEX = re.compile(
    r"博彩|赌场|真人荷官|下注|体育投注|百家乐"
    r"|成人直播|裸聊|约炮|色情|梯子|翻墙|赌球"
    r"|极速提现|棋牌|六合彩|老虎机|皇冠"
    r"|福布斯公司|福布斯|开户|上分|下分|微信同步|注册|开户上分"
    ,re.I
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