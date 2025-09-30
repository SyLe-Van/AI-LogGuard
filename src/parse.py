import re

def basic_parse(logs_text: str, build_status: str = 'UNKNOWN', format: str = 'text') -> str:
    """
    Parse logs Jenkins nâng cao:
    - Đếm chính xác số errors/warnings, tránh trùng lặp (bỏ các dòng script như '+ echo ...').
    - Trích xuất top errors/warnings sạch, ưu tiên mức độ nghiêm trọng, thêm context stage.
    - Check trạng thái build (SUCCESS/FAILURE).
    - Output rõ ràng, dễ đọc hoặc JSON nếu format='json'.
    """
    import re
    from collections import OrderedDict
    import json

    lines = logs_text.splitlines()
    # Regex nâng cao cho error/warning
    error_patterns = [r'\[ERROR\]', r'\berror\b', r'\berr\b', r'\bfailed\b', r'\bFAILURE\b', r'error:.*', r'fail:.*', r'exception:.*']
    warning_patterns = [r'\[WARNING\]', r'\bwarning\b']

    # Lọc các dòng thực thi script (bắt đầu bằng '+ ')
    real_lines = [l for l in lines if not l.strip().startswith('+')]

    # Lưu context stage cho từng dòng
    stage = None
    line_context = []
    for l in real_lines:
        l_strip = l.strip()
        # Cập nhật stage context
        m = re.match(r"\[Pipeline\] \{ \(([^)]+)\)", l_strip)
        if m:
            stage = m.group(1)
        line_context.append((l_strip, stage))

    # Đếm và gom errors/warnings, chuẩn hóa lowercase để tránh lặp
    error_dict = OrderedDict()
    warning_dict = OrderedDict()
    for l, stg in line_context:
        l_norm = l.lower()
        # Error
        if any(re.search(pat, l_norm, re.IGNORECASE) for pat in error_patterns):
            # Loại bỏ các dòng chỉ là "error:" hoặc "failed:" không có nội dung
            if l_norm.strip() not in error_dict:
                error_dict[l_norm.strip()] = (l, stg)
        # Warning
        if any(re.search(pat, l_norm, re.IGNORECASE) for pat in warning_patterns):
            if l_norm.strip() not in warning_dict:
                warning_dict[l_norm.strip()] = (l, stg)

    errors_count = len(error_dict)
    warnings_count = len(warning_dict)

    # Sắp xếp errors theo mức độ: FAILED > ERROR > [ERROR] > error > err
    def error_priority(e):
        l = e[0].lower()
        if 'failed' in l: return 0
        if '[error]' in l: return 1
        if 'error' in l: return 2
        if 'err' in l: return 3
        return 4
    sorted_errors = sorted(error_dict.values(), key=error_priority)

    # Sắp xếp warnings theo thứ tự xuất hiện
    sorted_warnings = list(warning_dict.values())

    # Trích xuất top 5 errors, top 3 warnings
    top_errors = sorted_errors[:5]
    top_warnings = sorted_warnings[:3]

    # Check trạng thái build nếu chưa truyền vào
    if build_status == 'UNKNOWN':
        for l in reversed(lines):
            if 'Finished: SUCCESS' in l:
                build_status = 'SUCCESS'
                break
            elif 'Finished: FAILURE' in l or 'Finished: FAILED' in l:
                build_status = 'FAILURE'
                break

    if format == 'json':
        data = {
            'build_status': build_status,
            'errors_count': errors_count,
            'warnings_count': warnings_count,
            'top_errors': [err for err, _ in top_errors],
            'top_warnings': [warn for warn, _ in top_warnings]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    # Xây dựng output tóm tắt dạng text
    summary = f"Summary of Logs\nBuild Status: {build_status}\n"
    summary += f"Total Errors/Failures: {errors_count}\n"
    summary += f"Total Warnings: {warnings_count}\n"
    if top_errors:
        summary += "Top Errors/Failures:\n"
        for err, stg in top_errors:
            if stg:
                summary += f"- [Stage: {stg}] {err}\n"
            else:
                summary += f"- {err}\n"
    else:
        summary += "No errors found.\n"
    if top_warnings:
        summary += "Top Warnings:\n"
        for warn, stg in top_warnings:
            if stg:
                summary += f"- [Stage: {stg}] {warn}\n"
            else:
                summary += f"- {warn}\n"
    return summary.strip()