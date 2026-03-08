import base64
from rules.rules import BASE64_PATTERN, CHARCODE_PATTERN


def decode_base64(text):
    results = []
    matches = BASE64_PATTERN.findall(text)
    for m in matches:
        if len(m) % 4 != 0:
            continue
        try:
            decoded = base64.b64decode(m).decode(errors="ignore")
            results.append(decoded)
        except:
            pass
    return results


def decode_charcode(js):
    results = []
    matches = CHARCODE_PATTERN.findall(js)
    for m in matches:
        try:
            nums = m.split(",")
            chars = [chr(int(x.strip())) for x in nums]
            results.append("".join(chars))
        except:
            pass
    return results