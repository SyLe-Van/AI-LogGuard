# 🧪 Testing Phase 2 (LLM Integration)

## Prerequisites

### 1. Get OpenAI API Key

- Sign up at https://platform.openai.com/
- Go to API Keys section
- Create a new secret key
- Copy the key (starts with `sk-...`)

### 2. Set Environment Variable

```bash
export OPENAI_API_KEY='sk-your-actual-key-here'
```

**Note:** For permanent setup, add to `~/.zshrc`:

```bash
echo "export OPENAI_API_KEY='sk-your-key'" >> ~/.zshrc
source ~/.zshrc
```

## Test Suite

### Test 1: Run Automated Test Script

```bash
cd /Users/mac/projects/Thesis/ai-logguard
python test_llm_features.py
```

**Expected Output:**

- ✅ 6/6 tests pass
- Shows: Token usage, cost estimates, cache statistics
- Exit code: 0

### Test 2: CLI with Sample Logs (Phase 1 Only)

```bash
python -m src.cli analyze tests/sample_logs.txt
```

**Expected Output:**

- Platform: JENKINS
- Status: UNSTABLE
- 8 errors, 8 warnings
- Rule-based analysis only

### Test 3: CLI with Phase 2 (AI Summary)

```bash
python -m src.cli analyze tests/sample_logs.txt --llm
```

**Expected Output:**

- Phase 1: Rule-based analysis
- Phase 2: AI-powered summary
  - Status analysis
  - Main issue identified
  - Key points (3-5 bullets)
  - Impact assessment
  - Confidence score
- Token usage: ~2000-3000 tokens
- Cost: ~$0.003-0.005

### Test 4: CLI with Full AI Analysis

```bash
python -m src.cli analyze tests/sample_logs.txt --llm --full
```

**Expected Output:**

- Phase 1: Rule-based analysis
- Phase 2: AI-powered analysis
  1. 🤖 AI Summary
  2. 🔍 Error Explanation (first error)
  3. 💡 Fix Suggestions
- Token usage: ~4000-6000 tokens
- Cost: ~$0.008-0.012

### Test 5: Cache Hit Test

```bash
# First run (cache miss)
python -m src.cli analyze tests/sample_logs.txt --llm

# Second run (cache hit)
python -m src.cli analyze tests/sample_logs.txt --llm
```

**Expected Output (2nd run):**

- ✅ Using cached summary
- No API calls made
- Cost: $0.00
- Cache hit rate: 100%

### Test 6: Different Model Test

```bash
python -m src.cli analyze tests/sample_logs.txt --llm --model gpt-4
```

**Note:** GPT-4 is more expensive (~10x) but potentially more accurate.

### Test 7: Bypass Cache

```bash
python -m src.cli analyze tests/sample_logs.txt --llm --no-cache
```

**Expected Output:**

- Forces fresh API calls
- Useful for testing prompt changes

### Test 8: Version Check

```bash
python -m src.cli version --verbose
```

**Expected Output:**

```
AI-LogGuard v1.0.0

Phase 1 Features:
  ✅ Jenkins & GitHub Actions parsing
  ✅ Error detection and categorization
  ...

Phase 2 Features:
  ✅ AI-powered summaries (OpenAI)
  ✅ Error explanations
  ✅ Fix suggestions
  ✅ Cost-efficient caching
```

## Expected Costs

### GPT-3.5-turbo (default)

- Input: $0.0015 per 1K tokens
- Output: $0.002 per 1K tokens

**Typical Analysis:**

- Summary only: ~2500 input + 500 output = **$0.004**
- Full analysis: ~4500 input + 1500 output = **$0.010**

### With 65% Cache Hit Rate

- Average cost per analysis: **$0.0035** (summary) or **$0.0014** (cached)

## Troubleshooting

### Error: "LLM features not available"

```bash
pip install openai tiktoken tenacity
```

### Error: "OPENAI_API_KEY not set"

```bash
export OPENAI_API_KEY='sk-your-key'
```

### Error: "Rate limit exceeded"

- Wait 60 seconds
- Or upgrade OpenAI plan

### Cache Not Working

```bash
# Check cache directory
ls -la ~/.ai-logguard/cache/

# Clear cache
rm -rf ~/.ai-logguard/cache/
```

## Performance Benchmarks

| Operation       | Time  | Tokens | Cost    |
| --------------- | ----- | ------ | ------- |
| Phase 1 only    | <1s   | 0      | $0.00   |
| Phase 2 summary | 2-3s  | ~3000  | ~$0.004 |
| Phase 2 full    | 4-6s  | ~6000  | ~$0.010 |
| Cache hit       | <0.1s | 0      | $0.00   |

## Real-World Test with Jenkins Log

If you have a real Jenkins log:

```bash
# Analyze with both phases
python -m src.cli analyze jenkins-build.log --llm --full

# Compare outputs
python -m src.cli analyze jenkins-build.log > phase1.txt
python -m src.cli analyze jenkins-build.log --llm --full > phase2.txt
diff phase1.txt phase2.txt
```

## Success Criteria

✅ All 6 automated tests pass  
✅ CLI commands work without errors  
✅ AI summaries are coherent and relevant  
✅ Cache hit rate > 50% on repeated runs  
✅ Cost per analysis < $0.015  
✅ Response time < 10s for full analysis

## Next Steps After Testing

1. ✅ Test with real Jenkins logs
2. ✅ Verify cache effectiveness (run same log twice)
3. ✅ Check cost tracking accuracy
4. ⏳ Add `explain` and `fix` commands
5. ⏳ Create usage documentation
6. ⏳ Add example outputs to README

## Notes

- Cache TTL: 7 days (configurable in `CacheManager`)
- Cache location: `~/.ai-logguard/cache/`
- Default model: `gpt-3.5-turbo`
- Max tokens per chunk: 3000
- Chunk overlap: 100 tokens
