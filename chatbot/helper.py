import re

def clean_json(s):
    s = re.sub(r',\s*([}\]])', r'\1', s)
    s = re.sub(r'\[\s*(https?://[^\s\]]+?)\s*,\s*\]', r'"\1"', s)
    s = re.sub(r'"(\[https?://[^\]]+\])"', r'"\1"', s)
    return s