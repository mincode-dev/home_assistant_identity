import re

def strip_candid_comments(src: str) -> str:
    """Remove // line and /* block */ comments."""
    src = re.sub(r"//.*?$", "", src, flags=re.M)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return src

def iter_balanced_blocks(src: str, keyword: str):
    """
    Yield inner text for '<keyword> { ... }' blocks with nested braces handled.
    Works for 'record' and 'variant'.
    """
    i, n = 0, len(src)
    kw = keyword
    while i < n:
        j = src.find(kw, i)
        if j < 0:
            break
        k = j + len(kw)
        while k < n and src[k].isspace():
            k += 1
        if k >= n or src[k] != "{":
            i = j + 1
            continue
        depth, start = 0, k + 1
        k += 1
        while k < n:
            c = src[k]
            if c == "{":
                depth += 1
            elif c == "}":
                if depth == 0:
                    yield src[start:k]
                    i = k + 1
                    break
                depth -= 1
            k += 1
        else:
            break
