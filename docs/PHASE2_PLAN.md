# 🤖 PHASE 2: LLM Integration

## 📋 Tổng Quan

**Phase 2** tích hợp **Large Language Model (OpenAI GPT)** vào AI-LogGuard để cung cấp khả năng:

- ✨ **Tóm tắt logs** thông minh
- 🔍 **Giải thích errors** chi tiết
- 💡 **Đề xuất fix** cụ thể

**Thời gian:** 2 tuần (Tuần 3-4)

---

## 🎯 Mục Tiêu Phase 2

### Input:

- ✅ **ParsedLog** từ Phase 1 (đã có từ Jenkins/GitHub Actions parser)
- ✅ Raw log content đã được parse

### Output:

- ✨ **Log Summary** - Tóm tắt 3-5 điểm chính
- 🔍 **Error Explanation** - Giải thích chi tiết lỗi
- 💡 **Fix Suggestions** - Các bước fix cụ thể với code examples

### Công nghệ:

- **OpenAI API** (GPT-3.5-turbo hoặc GPT-4)
- **Prompt Engineering** - Thiết kế prompts hiệu quả
- **Caching** - Giảm cost API
- **Token Management** - Xử lý logs dài

---

## 📊 Architecture Phase 2

```
┌─────────────────────────────────────────────────────────────┐
│                     Phase 1 (Completed)                     │
│  Raw Log → Parser → ParsedLog (errors, warnings, stages)    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                        Phase 2 (NEW)                        │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │   Chunker    │ →    │  Prompt      │                   │
│  │ (Split logs) │      │  Templates   │                   │
│  └──────────────┘      └──────────────┘                   │
│                              ↓                              │
│                     ┌─────────────────┐                    │
│                     │  OpenAI Client  │                    │
│                     │  (with retry)   │                    │
│                     └─────────────────┘                    │
│                              ↓                              │
│         ┌────────────────────┼────────────────────┐        │
│         ↓                    ↓                    ↓        │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐    │
│  │Summarizer│        │Explainer │        │  Fixer   │    │
│  └──────────┘        └──────────┘        └──────────┘    │
│         │                    │                    │        │
│         └────────────────────┴────────────────────┘        │
│                              ↓                              │
│                        ┌──────────┐                        │
│                        │  Cache   │                        │
│                        │  Manager │                        │
│                        └──────────┘                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    📄 Enhanced Output
                  (Summary + Explanations + Fixes)
```

---

## 📝 Tasks Chi Tiết

### ✅ Week 3: OpenAI Integration & Core Features

#### Task 3.1: OpenAI Client Setup (2-3 giờ)

**Files:**

- `src/llm/__init__.py`
- `src/llm/openai_client.py`

**Features:**

- ✅ Setup OpenAI API client
- ✅ API key management (.env)
- ✅ Retry logic with exponential backoff
- ✅ Rate limiting
- ✅ Error handling

**Dependencies:**

```bash
pip install openai python-dotenv tenacity
```

**Code Structure:**

```python
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    @retry(stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3  # Lower temp for consistent output
        )
        return response.choices[0].message.content
```

---

#### Task 3.2: Prompt Templates (6-8 giờ)

**Files:**

- `src/llm/prompts.py`

**Prompts to create:**

**1. Summarization Prompt:**

```python
SUMMARIZE_PROMPT = """
You are a CI/CD DevOps expert analyzing build logs.

Analyze this {platform} build log and provide:
1. **Status**: What happened (success/failed/timeout)
2. **Main Issue**: Primary problem in 1 sentence
3. **Key Points**: 3-5 bullet points
4. **Impact**: Severity (Low/Medium/High/Critical)

Build Info:
- Platform: {platform}
- Job: {job_name}
- Status: {status}
- Errors: {error_count}
- Warnings: {warning_count}

Log Content:
{log_content}

Provide concise, actionable summary.
"""
```

**2. Error Explanation Prompt:**

```python
EXPLAIN_ERROR_PROMPT = """
You are a DevOps expert. Explain this CI/CD error in detail.

Error Information:
- Type: {error_type}
- Message: {error_message}
- Line: {line_number}
- Platform: {platform}

Context:
{context}

Provide:
1. **Root Cause**: Why this error occurred
2. **Common Scenarios**: When does this typically happen
3. **Technical Details**: What's happening under the hood

Be specific and technical but clear.
"""
```

**3. Fix Suggestion Prompt:**

```python
FIX_SUGGESTION_PROMPT = """
You are a DevOps engineer. Provide fix steps for this build error.

Error Summary:
{error_summary}

Build Context:
- Platform: {platform}
- Job: {job_name}
- Environment: {environment}

Error Details:
{error_details}

Provide:
1. **Quick Fix** (if available): Immediate action
2. **Detailed Steps**: 3-5 numbered steps
3. **Code Changes** (if needed): Specific code/config
4. **Prevention**: How to avoid this in future

Format steps clearly with code examples where helpful.
"""
```

---

#### Task 3.3: Log Chunking Strategy (4-5 giờ)

**Files:**

- `src/llm/chunker.py`

**Problem:** GPT-3.5 có limit 4k tokens. Logs lớn cần split.

**Strategy:**

1. Extract error sections (priority cao)
2. Chunk remaining content
3. Each chunk ≤ 3000 tokens (safe margin)
4. Overlap 100 tokens giữa chunks

**Code:**

```python
import tiktoken

class LogChunker:
    def __init__(self, model: str = "gpt-3.5-turbo", max_tokens: int = 3000):
        self.encoding = tiktoken.encoding_for_model(model)
        self.max_tokens = max_tokens

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def chunk_log(self, parsed_log: ParsedLog) -> List[str]:
        # Priority: Errors first
        chunks = []

        # Chunk 1: Metadata + errors
        error_section = self._build_error_section(parsed_log)
        chunks.append(error_section)

        # Chunk 2+: Remaining content
        if self.count_tokens(parsed_log.raw_content) > self.max_tokens:
            chunks.extend(self._split_content(parsed_log.raw_content))

        return chunks
```

---

#### Task 3.4: LLM Summarizer (5-6 giờ)

**Files:**

- `src/llm/summarizer.py`

**Features:**

- Summarize parsed logs
- Handle multi-chunk logs
- Cache results
- Format output

**Code Structure:**

```python
from dataclasses import dataclass

@dataclass
class LogSummary:
    status: str
    main_issue: str
    key_points: List[str]
    impact: str
    confidence: float

class LogSummarizer:
    def __init__(self, client: OpenAIClient, chunker: LogChunker):
        self.client = client
        self.chunker = chunker

    def summarize(self, parsed_log: ParsedLog) -> LogSummary:
        # Build prompt
        prompt = self._build_prompt(parsed_log)

        # Call LLM
        response = self.client.generate(prompt, max_tokens=500)

        # Parse response
        return self._parse_summary(response)
```

---

#### Task 3.5: Error Explainer (5-6 giờ)

**Files:**

- `src/llm/explainer.py`

**Features:**

- Explain individual errors
- Batch processing for multiple errors
- Context-aware explanations

**Output:**

```python
@dataclass
class ErrorExplanation:
    error_message: str
    root_cause: str
    common_scenarios: List[str]
    technical_details: str
    related_docs: List[str]  # Optional
```

---

#### Task 3.6: Fix Suggestion Generator (6-7 giờ)

**Files:**

- `src/llm/fix_suggester.py`

**Features:**

- Generate actionable fix steps
- Platform-specific suggestions
- Code examples when relevant
- Confidence scoring

**Output:**

```python
@dataclass
class FixPlan:
    diagnosis: str
    quick_fix: Optional[str]
    detailed_steps: List[str]
    code_changes: Dict[str, str]  # file → code
    prevention_tips: List[str]
    confidence: float
```

---

### ✅ Week 4: Optimization & Polish

#### Task 4.1: Caching System (5-6 giờ)

**Files:**

- `src/cache/cache_manager.py`

**Features:**

- Hash-based caching (SHA256 of log content)
- TTL (time-to-live) - 7 days default
- Disk-based cache (~/.ai-logguard/cache/)
- Cache stats

**Code:**

```python
import hashlib
import pickle
from pathlib import Path

class CacheManager:
    def __init__(self, cache_dir: Path, ttl: int = 604800):
        self.cache_dir = cache_dir
        self.ttl = ttl

    def cache_key(self, log_content: str) -> str:
        return hashlib.sha256(log_content.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        # Check cache, validate TTL
        pass

    def set(self, key: str, value: Any):
        # Save to disk
        pass
```

**Expected:** 50-70% cache hit rate after some usage

---

#### Task 4.2: Cost Tracking (3-4 giờ)

**Files:**

- `src/llm/cost_tracker.py`

**Features:**

- Track tokens used
- Calculate cost (GPT-3.5: $0.002/1K tokens)
- Daily/monthly limits
- Usage report

**Output:**

```
📊 API Usage Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Today:
  Requests: 45
  Tokens: 125,340
  Est. Cost: $0.25
  Cache Hits: 65%

This Month:
  Requests: 1,234
  Tokens: 3,456,789
  Est. Cost: $6.91
```

---

#### Task 4.3: CLI Integration (4-5 giờ)

**Update files:**

- `src/cli.py`

**New commands:**

```bash
# Summarize with LLM
ai-logguard summarize jenkins-test.log --llm

# Explain errors
ai-logguard explain jenkins-test.log

# Suggest fixes
ai-logguard fix jenkins-test.log

# Combined analysis
ai-logguard analyze jenkins-test.log --full --llm
```

**Flags:**

- `--llm` - Enable LLM features
- `--no-cache` - Bypass cache
- `--model gpt-4` - Use specific model

---

#### Task 4.4: Output Formatting (4-5 giờ)

**Update:**

- `src/utils/display.py`

**Enhanced output:**

```
╭────────────────────── 🤖 AI Analysis ──────────────────────╮
│                                                            │
│ 📋 Summary                                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│ Status: ❌ Build Failed                                    │
│ Main Issue: Docker build failed due to dependency error   │
│                                                            │
│ Key Points:                                                │
│  • npm package 'react@18.0.0' not found                   │
│  • Package registry timeout during install                │
│  • Build terminated at step 3/12                          │
│                                                            │
│ Impact: 🔴 High - Blocks deployment                        │
╰────────────────────────────────────────────────────────────╯

╭────────────────── 🔍 Error Explanation ────────────────────╮
│                                                            │
│ Root Cause:                                                │
│ The build failed because npm cannot resolve the React     │
│ dependency. This is likely due to:                        │
│  1. Network timeout to npm registry                       │
│  2. Invalid package version specification                 │
│  3. Private registry misconfiguration                     │
│                                                            │
│ Common Scenarios:                                          │
│  • npm registry downtime                                  │
│  • Firewall blocking registry access                      │
│  • Typo in package.json version                           │
╰────────────────────────────────────────────────────────────╯

╭──────────────────── 💡 Fix Suggestions ────────────────────╮
│                                                            │
│ Quick Fix:                                                 │
│ $ npm cache clean --force                                 │
│ $ npm install --registry=https://registry.npmjs.org       │
│                                                            │
│ Detailed Steps:                                            │
│ 1. Clear npm cache:                                       │
│    npm cache clean --force                                │
│                                                            │
│ 2. Verify package.json:                                   │
│    Check that react version is valid                      │
│                                                            │
│ 3. Try with explicit registry:                            │
│    npm install --registry=https://registry.npmjs.org      │
│                                                            │
│ 4. If still failing, add to .npmrc:                       │
│    registry=https://registry.npmjs.org                    │
│    fetch-timeout=60000                                    │
│                                                            │
│ Prevention:                                                │
│  • Pin package versions in package-lock.json              │
│  • Use local npm cache mirror                             │
│  • Set timeout in .npmrc                                  │
│                                                            │
│ Confidence: 🟢 85%                                         │
╰────────────────────────────────────────────────────────────╯
```

---

#### Task 4.5: Testing & Documentation (6-8 giờ)

**Tests:**

- Unit tests cho mỗi component
- Integration tests
- Mock OpenAI API cho testing
- Cost tracking tests

**Documentation:**

- `docs/LLM_INTEGRATION.md` - Setup guide
- `docs/PROMPTS.md` - Prompt engineering notes
- Update README.md
- Add examples

---

## 📦 Dependencies

**New packages cần install:**

```bash
pip install openai python-dotenv tenacity tiktoken
```

**Update requirements.txt:**

```
# Phase 1 (existing)
typer>=0.9.0
rich>=13.0.0
pydantic>=2.0.0
requests>=2.31.0
pytest>=7.4.0

# Phase 2 (new)
openai>=1.0.0
python-dotenv>=1.0.0
tenacity>=8.2.0
tiktoken>=0.5.0
```

---

## 💰 Cost Estimation

**GPT-3.5-turbo pricing:**

- Input: $0.0015 / 1K tokens
- Output: $0.002 / 1K tokens

**Per analysis:**

- Input: ~2K tokens (log chunk)
- Output: ~500 tokens (summary + explanation + fixes)
- Cost: ~$0.004 per analysis

**With caching (65% hit rate):**

- 100 analyses: ~$1.40
- 1000 analyses: ~$14.00

**GPT-4 (nếu dùng):**

- 10x expensive hơn
- Chỉ dùng cho complex cases

---

## 🎯 Success Criteria

Phase 2 considered **complete** khi:

✅ **Functionality:**

- [ ] LLM summarizer hoạt động với accuracy >80%
- [ ] Error explanations rõ ràng, hữu ích
- [ ] Fix suggestions actionable, có code examples
- [ ] Xử lý được logs >5000 lines

✅ **Performance:**

- [ ] Summarize trong <5s (với cache)
- [ ] Full analysis trong <15s
- [ ] Cache hit rate >50% sau 1 tuần dùng

✅ **Cost:**

- [ ] Average cost <$0.01 per analysis
- [ ] Cost tracking accurate
- [ ] Budget warnings work

✅ **Quality:**

- [ ] Outputs are professional, readable
- [ ] CLI commands intuitive
- [ ] Error handling robust
- [ ] Documentation complete

---

## 🚀 Next Steps

**Sau khi Phase 2 hoàn thành:**

1. **Test với real users** - Gather feedback
2. **Optimize prompts** - Improve based on results
3. **Phase 3** - ML model training (hybrid approach)
4. **Phase 4** - Deployment & production ready

---

## 📝 Notes

**Tips:**

- Start với GPT-3.5-turbo (cheaper, faster)
- Optimize prompts carefully (token costs)
- Cache aggressively
- Monitor API usage closely

**Potential Issues:**

- API rate limits (handle gracefully)
- Cost overruns (set limits)
- Prompt quality (iterate)
- Token limits (chunk properly)

---

Generated: {{ datetime.now() }}
Phase 2 Duration: 2 weeks (80-100 hours)
