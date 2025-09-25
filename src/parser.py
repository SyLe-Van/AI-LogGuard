import re

def parse_with_regex(text, pattern):
    return re.findall(pattern, text)
