# 🎉 Ollama Setup Guide (100% FREE!)

## Why Ollama?

- ✅ **Completely FREE** - No API costs, no rate limits
- ✅ **Private** - Your data never leaves your machine
- ✅ **Fast** - No network latency
- ✅ **High Quality** - Llama 3.1, Mistral, CodeLlama models
- ✅ **No API Keys** - Just install and run

## Quick Start (5 minutes)

### Step 1: Install Ollama

**macOS/Linux:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from https://ollama.com/download

**Manual:**
Visit https://ollama.com/download and choose your OS

### Step 2: Start Ollama Server

```bash
ollama serve
```

_Keep this terminal open. Ollama runs in the background._

### Step 3: Download a Model

**Recommended (Best Quality):**

```bash
ollama pull llama3.1:8b  # 4.7GB, best quality
```

**Alternative Models:**

```bash
ollama pull mistral:7b    # 4.1GB, faster
ollama pull codellama:7b  # 3.8GB, good for code analysis
```

### Step 4: Test It!

```bash
cd /Users/mac/projects/Thesis/ai-logguard
python -m src.cli analyze tests/sample_logs.txt --llm
```

**Expected output:**

- ✅ Ollama ready
- 🤖 AI-powered analysis
- 💰 Cost: $0.00 (FREE!)

## Usage

### Basic Analysis (Phase 1 - Free)

```bash
python -m src.cli analyze my-log.txt
```

### AI Analysis (Phase 2 - Also Free!)

```bash
python -m src.cli analyze my-log.txt --llm
```

### Full AI Analysis

```bash
python -m src.cli analyze my-log.txt --llm --full
```

### Choose Different Model

```bash
# Use Mistral (faster)
python -m src.cli analyze my-log.txt --llm --model mistral:7b

# Use CodeLlama (best for code)
python -m src.cli analyze my-log.txt --llm --model codellama:7b
```

## Available Models

| Model           | Size  | Speed  | Quality   | Best For        |
| --------------- | ----- | ------ | --------- | --------------- |
| **llama3.1:8b** | 4.7GB | Medium | Best      | General use ⭐  |
| mistral:7b      | 4.1GB | Fast   | Good      | Quick analysis  |
| codellama:7b    | 3.8GB | Medium | Good      | Code errors     |
| llama3:latest   | 4.7GB | Medium | Excellent | Latest features |
| mistral:latest  | 4.1GB | Fast   | Good      | Speed priority  |

## Troubleshooting

### Error: "Cannot connect to Ollama"

**Solution:**

```bash
# Check if Ollama is running
ollama list

# If not, start it
ollama serve
```

### Error: "Model 'llama3.1:8b' not found"

**Solution:**

```bash
# Download the model
ollama pull llama3.1:8b

# Check available models
ollama list
```

### Ollama Not Found

**Solution:**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### Slow Performance

**Options:**

1. Use smaller model: `mistral:7b` (faster)
2. Use quantized model: `llama3.1:8b-q4` (smaller, faster)
3. Close other apps to free RAM

### Model Download Failed

**Solution:**

```bash
# Try again with more specific version
ollama pull llama3.1:8b-instruct-q4_0

# Or use smaller model
ollama pull mistral:7b
```

## Advanced Usage

### Auto-start Ollama (macOS)

Create `~/Library/LaunchAgents/com.ollama.serve.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.serve</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Then:

```bash
launchctl load ~/Library/LaunchAgents/com.ollama.serve.plist
```

### Check Ollama Status

```bash
# List running models
ollama ps

# List downloaded models
ollama list

# Show model info
ollama show llama3.1:8b

# Test with simple prompt
ollama run llama3.1:8b "Explain CI/CD in one sentence"
```

### Manage Storage

```bash
# Remove unused model
ollama rm old-model:tag

# Pull specific version
ollama pull llama3.1:8b-instruct-q4_0
```

## Performance Benchmarks

| Operation                | Time  | Cost  |
| ------------------------ | ----- | ----- |
| Phase 1 only             | <1s   | $0.00 |
| Phase 2 summary (Ollama) | 3-8s  | $0.00 |
| Phase 2 full (Ollama)    | 8-15s | $0.00 |
| Cache hit                | <0.1s | $0.00 |

_Times vary based on hardware and model size_

## Comparison: OpenAI vs Ollama

| Feature      | OpenAI             | Ollama                   |
| ------------ | ------------------ | ------------------------ |
| **Cost**     | $0.004/analysis    | **$0.00 FREE** ✅        |
| **Privacy**  | Data sent to cloud | **Stays local** ✅       |
| **Speed**    | 2-3s               | 3-8s                     |
| **Quality**  | Excellent          | Very Good ⭐             |
| **Setup**    | API key needed     | **1-command install** ✅ |
| **Limits**   | Rate limits        | **No limits** ✅         |
| **Internet** | Required           | **Works offline** ✅     |

## System Requirements

**Minimum:**

- RAM: 8GB
- Storage: 5GB free
- CPU: Any modern processor

**Recommended:**

- RAM: 16GB+ (for better performance)
- Storage: 10GB+ (for multiple models)
- CPU: Apple Silicon or modern Intel/AMD

**Ideal:**

- RAM: 32GB+
- GPU: Apple M1/M2/M3 or NVIDIA GPU
- Storage: SSD with 20GB+ free

## FAQ

**Q: Is Ollama really free?**
A: Yes! 100% free, open-source, no hidden costs.

**Q: How does quality compare to GPT-4?**
A: Llama 3.1 is close to GPT-3.5 quality, suitable for most use cases.

**Q: Can I use both OpenAI and Ollama?**
A: Currently, AI-LogGuard uses Ollama by default. OpenAI support can be added if needed.

**Q: Does it work offline?**
A: Yes! Once models are downloaded, no internet needed.

**Q: How much disk space do I need?**
A: ~5GB per model. Llama3.1:8b = 4.7GB.

**Q: Can I switch models?**
A: Yes! Use `--model mistral:7b` or any other model you've downloaded.

## Next Steps

1. ✅ Install Ollama
2. ✅ Download llama3.1:8b
3. ✅ Test with sample logs
4. ✅ Analyze real Jenkins logs
5. 🎉 Enjoy free AI analysis!

## Resources

- Ollama Website: https://ollama.com
- Model Library: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama
- Discord Community: https://discord.gg/ollama

---

**Need help?** Check our troubleshooting section or file an issue!

**Pro tip:** Ollama + AI-LogGuard = Free, private, powerful CI/CD log analysis! 🚀
