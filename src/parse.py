import re
from collections import defaultdict, Counter

def basic_parse(logs_text: str, build_status: str = 'UNKNOWN', format: str = 'text') -> str:
    """
    Format Jenkins Build Summary with Stage Summary, Retry Count, Jenkins Mark vs. Summary, Top Errors/Warnings.
    """
    RED = "\033[31m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    RESET = "\033[0m"

    lines = logs_text.splitlines()
    stage = None
    stage_status = defaultdict(lambda: {'errors': 0, 'warnings': 0, 'retries': 0, 'status': 'SUCCESS', 'critical': 0})
    error_list, warning_list, retry_details = [], [], []
    retry_count = 0
    jenkins_mark, summary_status = None, 'SUCCESS'

    # Regex patterns
    stage_pat = re.compile(r"\[Pipeline\] \{ \(([^)]+)\)")
    error_pat = re.compile(r"(\[ERROR\]|\bFAILED\b|\bFAILURE\b|compilation failed|dependency|timeout|deployment failed|unit test failed|db connection timeout|critical error|2 critical errors)", re.IGNORECASE)
    warning_pat = re.compile(r"(\[WARNING\]|warning:|deprecated|flaky|slow response|large package|unstable|disk space|health check|certificate|rate limit)", re.IGNORECASE)
    retry_pat = re.compile(r"retry|retried|re-try|try again|flaky", re.IGNORECASE)
    retry_type_pat = re.compile(r"(dependency|db|database|deploy|connection|fetch|unit test|integration|build|checkout|package|test|api|probe|health)", re.IGNORECASE)
    status_pat = re.compile(r"Finished: (SUCCESS|FAILURE|UNSTABLE)", re.IGNORECASE)
    critical_pat = re.compile(r"critical|2 critical errors", re.IGNORECASE)

    # Parse logs
    for l in lines:
        l_strip = l.strip()
        if l_strip.startswith('+ echo'):
            continue

        if mstat := status_pat.search(l_strip):
            jenkins_mark = mstat.group(1).upper()

        if mstage := stage_pat.match(l_strip):
            stage = mstage.group(1)

        if error_pat.search(l_strip):
            error_list.append(l_strip)
            if stage:
                stage_status[stage]['errors'] += 1
                if critical_pat.search(l_strip):
                    stage_status[stage]['critical'] += 1
            else:
                stage_status['Unknown']['errors'] += 1
            summary_status = 'UNSTABLE'

        if warning_pat.search(l_strip):
            warning_list.append(l_strip)
            if stage:
                stage_status[stage]['warnings'] += 1
            else:
                stage_status['Unknown']['warnings'] += 1
            if summary_status == 'SUCCESS':
                summary_status = 'UNSTABLE'

        if retry_pat.search(l_strip):
            retry_count += 1
            mtype = retry_type_pat.search(l_strip)
            retry_label = mtype.group(1).capitalize() if mtype else 'Other'
            retry_details.append(retry_label)
            if stage:
                stage_status[stage]['retries'] += 1

        if stage and ("FAILED" in l_strip or "FAILURE" in l_strip):
            stage_status[stage]['status'] = 'FAILED'

    def unique_top(lst, n, prefix=None):
        seen, out = set(), []
        for x in lst:
            x_clean = re.sub(r'^\+ echo ', '', x)
            if prefix and not x_clean.strip().startswith(prefix):
                continue
            if x_clean not in seen:
                out.append(x_clean)
                seen.add(x_clean)
            if len(out) >= n:
                break
        return out

    top_errors = unique_top(error_list, 8, prefix='[ERROR]')
    top_warnings = unique_top(warning_list, 7, prefix='[WARNING]')

    seen_stages = []
    for l in lines:
        if mstage := stage_pat.match(l.strip()):
            stg = mstage.group(1)
            if stg not in seen_stages:
                seen_stages.append(stg)
    if not seen_stages:
        seen_stages = list(stage_status.keys())

    stage_lines = []
    for stg in seen_stages:
        info = stage_status[stg]
        line = f"- {stg:<20}: {info['status']}"
        extras = []
        if info['warnings']:
            extras.append(f"Warnings: {info['warnings']}")
        if info['errors']:
            extras.append(f"Errors: {info['errors']}")
        if info['retries']:
            extras.append(f"Retries: {info['retries']}")
        if info['critical']:
            extras.append(f"{RED}{info['critical']} CRITICAL{RESET}")
        if extras:
            line += " (" + ", ".join(extras) + ")"
        stage_lines.append(line)

    mismatch = jenkins_mark and (jenkins_mark != summary_status)
    mismatch_note = f"   (⚠ Mismatch: Summary marked {summary_status})" if mismatch else ""

    out = []
    out.append("="*49)
    out.append(" Jenkins Build Summary")
    out.append("="*49)
    # Màu cho status
    status_icon = ''
    if summary_status == 'SUCCESS':
        status_color = GREEN
        status_icon = '🌱'
    elif summary_status == 'UNSTABLE':
        status_color = YELLOW
        status_icon = '⚠'
    elif summary_status == 'FAILURE':
        status_color = RED
        status_icon = '❌'
    else:
        status_color = RESET
    out.append(f"Build Status : {status_color}{status_icon} {summary_status}{RESET}")
    # Jenkins Mark cũng có màu
    if jenkins_mark == 'SUCCESS':
        jm_color = GREEN
        jm_icon = '🌱'
    elif jenkins_mark == 'UNSTABLE':
        jm_color = YELLOW
        jm_icon = '⚠'
    elif jenkins_mark == 'FAILURE':
        jm_color = RED
        jm_icon = '❌'
    else:
        jm_color = RESET
        jm_icon = ''
    out.append(f"Jenkins Mark : {jm_color}{jm_icon} {jenkins_mark or 'UNKNOWN'}{RESET}{mismatch_note}")
    out.append(f"Errors       : {len(error_list)}")
    out.append(f"Warnings     : {len(warning_list)}")
    out.append(f"Retries      : {retry_count}")
    if retry_details:
        retry_counter = Counter(retry_details)
        out.append("Retries:")
        for label, cnt in retry_counter.items():
            out.append(f"  - {label}: {cnt}")
    out.append("-"*50)
    out.append("")
    out.append("Stage Summary:")
    out.extend(stage_lines or ["- No stage info found."])
    out.append("")
    out.append("-"*50)
    out.append("Top Errors / Failures:")
    if top_errors:
        for err in top_errors:
            if critical_pat.search(err):
                # Đảm bảo không lặp icon nếu đã có
                clean_err = err.replace('❌ [CRITICAL] ', '').replace('- ❌ [CRITICAL] ', '').lstrip('- ')
                out.append(f"- {RED}❌ [CRITICAL] {clean_err}{RESET}")
            else:
                out.append(f"- {err}")
        if len(error_list) > len(top_errors):
            out.append(f"... and {len(error_list) - len(top_errors)} more errors not shown")
    else:
        out.append("- None")
    out.append("")
    out.append("Top Warnings:")
    if top_warnings:
        for warn in top_warnings:
            out.append(f"- {warn}")
        if len(warning_list) > len(top_warnings):
            out.append(f"... and {len(warning_list) - len(top_warnings)} more warnings not shown")
    else:
        out.append("- None")
    out.append("")
    out.append("-"*50)
    out.append(f"Final Result: Build completed with {'WARNINGS and ERRORS' if error_list or warning_list else 'no issues.'}")
    if error_list or warning_list:
        out.append(f"{YELLOW}⚠ Requires attention before production deployment.{RESET}")
    out.append("="*49)
    return "\n".join(out)
