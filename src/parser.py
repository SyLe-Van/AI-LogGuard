import re

def parse_with_regex(text, pattern):
    matches = re.findall(pattern, text)
    return f"Parsed logs (mock):\n" + "\n".join(matches)
    
def basic_parse(logs_text):
    """Tóm tắt logs cơ bản, trả về chuỗi với prefix 'Parsed logs (mock):'."""
    # Giới hạn output để tránh in logs dài (100 ký tự đầu)
    max_length = 100
    if len(logs_text) > max_length:
        truncated_logs = logs_text[:max_length] + "..."
    else:
        truncated_logs = logs_text
    return f"Parsed logs (mock):\n{truncated_logs}"