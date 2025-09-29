import re

def parse_with_regex(text, pattern):
    """Tìm tất cả các chuỗi khớp với pattern trong text."""
    return re.findall(pattern, text)

def basic_parse(logs_text):
    """Tóm tắt logs cơ bản, trả về chuỗi với prefix 'Parsed logs (mock):'."""
    max_length = 100
    if len(logs_text) > max_length:
        truncated_logs = logs_text[:max_length] + "..."
    else:
        truncated_logs = logs_text
    return f"Parsed logs (mock):\n{truncated_logs}"