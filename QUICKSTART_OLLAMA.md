# 🚀 Quick Start: Test Ollama với AI-LogGuard

## Bước 1: Cài Ollama (1 phút)

```bash
# macOS
curl -fsSL https://ollama.com/install.sh | sh

# Hoặc download từ: https://ollama.com/download
```

## Bước 2: Khởi động Ollama Server (Terminal 1)

```bash
# Mở terminal mới và chạy:
ollama serve

# Giữ terminal này chạy!
# Bạn sẽ thấy: "Ollama is running"
```

## Bước 3: Download Model (Terminal 2)

```bash
# Mở terminal thứ 2 và chạy:
ollama pull llama3.1:8b

# Chờ download ~4.7GB (mất 2-5 phút tùy mạng)
# Chỉ cần làm 1 lần!
```

## Bước 4: Test AI-LogGuard

```bash
cd /Users/mac/projects/Thesis/ai-logguard

# Test Phase 1 (vẫn hoạt động bình thường)
python -m src.cli analyze tests/sample_logs.txt

# Test Phase 2 với Ollama (FREE!)
python -m src.cli analyze tests/sample_logs.txt --llm

# Test với full analysis
python -m src.cli analyze tests/sample_logs.txt --llm --full
```

## Expected Output

### Phase 2 với Ollama:

```
======================================================================
🤖 Phase 2: AI-Powered Analysis (FREE with Ollama)
======================================================================

⏳ Generating AI summary...
✅ Generated

╭─────────────── 🤖 AI Summary ───────────────╮
│ STATUS: UNSTABLE                            │
│                                             │
│ MAIN ISSUE:                                 │
│ Multiple test failures and dependency...    │
│                                             │
│ KEY POINTS:                                 │
│   • Dependency lib-xyz failed to fetch      │
│   • Unit test test_order_checkout failing   │
│   • Database connection timeouts detected   │
│                                             │
│ IMPACT: High                                │
│ CONFIDENCE: 85%                             │
╰─────────────────────────────────────────────╯

----------------------------------------------------------------------
🎉 Tokens: 3,247 | Cost: $0.00 (FREE!)
🤖 Model: llama3.1:8b (Ollama - Local & Free)
----------------------------------------------------------------------
```

## Troubleshooting

### Lỗi: "Ollama server not running"

```bash
# Terminal 1: Start server
ollama serve
```

### Lỗi: "Model 'llama3.1:8b' not found"

```bash
# Download model
ollama pull llama3.1:8b

# Check downloaded models
ollama list
```

### Ollama command not found

```bash
# Install lại
curl -fsSL https://ollama.com/install.sh | sh

# Verify
ollama --version
```

## Alternative Models

Nếu muốn thử models khác:

```bash
# Mistral (nhỏ hơn, nhanh hơn)
ollama pull mistral:7b
python -m src.cli analyze tests/sample_logs.txt --llm --model mistral:7b

# CodeLlama (tốt cho code analysis)
ollama pull codellama:7b
python -m src.cli analyze tests/sample_logs.txt --llm --model codellama:7b
```

## So Sánh: Before vs After

### ❌ Before (OpenAI)

```bash
export OPENAI_API_KEY='sk-...'  # Phải có key
python -m src.cli analyze log.txt --llm
# → Tốn $0.004 mỗi lần
```

### ✅ After (Ollama)

```bash
ollama serve  # Không cần key!
python -m src.cli analyze log.txt --llm
# → Miễn phí hoàn toàn! $0.00
```

## Performance

| Operation       | Time  | Cost     |
| --------------- | ----- | -------- |
| Phase 1 only    | <1s   | $0.00    |
| Phase 2 summary | 3-8s  | $0.00 ✅ |
| Phase 2 full    | 8-15s | $0.00 ✅ |
| Cache hit       | <0.1s | $0.00    |

## Next Steps

1. ✅ Cài Ollama
2. ✅ Download llama3.1:8b
3. ✅ Test với sample logs
4. 🎯 Test với real Jenkins logs
5. 📊 So sánh quality với Phase 1
6. 📝 Update thesis với Ollama results

## Tips

**Auto-start Ollama khi boot macOS:**

```bash
# Add to ~/.zshrc
echo 'ollama serve &' >> ~/.zshrc
```

**Check Ollama status:**

```bash
ollama ps      # Running models
ollama list    # Downloaded models
```

**Remove unused model:**

```bash
ollama rm old-model:tag
```

## Demo cho Thesis

Chuẩn bị demo:

```bash
# Terminal 1: Ollama server
ollama serve

# Terminal 2: Demo Phase 1
python -m src.cli analyze jenkins-real-log.txt

# Terminal 2: Demo Phase 2
python -m src.cli analyze jenkins-real-log.txt --llm --full

# Show comparison!
```

## Questions?

- Ollama docs: https://ollama.com
- Model library: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama

---

**TL;DR:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve  # Terminal 1
ollama pull llama3.1:8b  # Terminal 2
python -m src.cli analyze tests/sample_logs.txt --llm  # Test!
```

🎉 **Hoàn toàn miễn phí! Không cần API key!** 🎉
