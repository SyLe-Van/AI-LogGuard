#!/bin/bash

# 🔧 Hướng dẫn setup API key mới cho Phase 3 Hybrid Mode
# ========================================================

echo "🚨 API KEY CŨ BỊ LEAK - CẦN TẠO KEY MỚI"
echo ""
echo "📋 BƯỚC 1: Tạo API key mới"
echo "  1. Mở: https://aistudio.google.com/app/apikey"
echo "  2. Click 'Create API key'"
echo "  3. Copy key mới"
echo ""
echo "📋 BƯỚC 2: Thêm key vào .env file"
echo "  1. Tạo file .env (nếu chưa có):"
echo "     cp .env.example .env"
echo ""
echo "  2. Mở file .env và paste key của bạn:"
echo "     nano .env"
echo "     # Sửa dòng GEMINI_API_KEY=your_gemini_api_key_here"
echo ""
echo "📋 BƯỚC 3: Test hybrid mode"
echo "  python scripts/test_hybrid_mode.py"
echo ""
echo "⚠️  LƯU Ý: File .env đã được thêm vào .gitignore - key sẽ KHÔNG bị commit"
echo ""
