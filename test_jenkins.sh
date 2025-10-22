#!/bin/bash
# Test script for AI-LogGuard with real Jenkins

JENKINS_URL="http://18.141.38.4:8080/"
JENKINS_USER="syle"
JENKINS_TOKEN="11123a05c95df07c7c66cf9206edb8ca20"  # Thay bằng token thực
JOB_NAME="vucar-pipeline"            # Thay bằng job name thực
BUILD_NUMBER="60"         # hoặc số build cụ thể như "123"

# ===== COLORS =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Testing AI-LogGuard with Jenkins..."
echo ""

# Check if token is set
if [ "$JENKINS_TOKEN" = "YOUR_TOKEN_HERE" ]; then
    echo -e "${RED}❌ Error: Please set JENKINS_TOKEN in this script${NC}"
    echo ""
    echo "Steps to get token:"
    echo "1. Go to Jenkins → Click your name → Configure"
    echo "2. Scroll to 'API Token' section"
    echo "3. Click 'Add new Token' → Generate"
    echo "4. Copy token and paste it in this script"
    exit 1
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${RED}❌ Virtual environment not found. Run: python -m venv .venv${NC}"
    exit 1
fi

# Step 1: Fetch logs from Jenkins
echo ""
echo -e "${YELLOW}📥 Step 1: Fetching logs from Jenkins...${NC}"
echo "URL: $JENKINS_URL"
echo "Job: $JOB_NAME"
echo "Build: $BUILD_NUMBER"
echo ""

python -m src.cli fetch \
  --provider jenkins \
  --url "$JENKINS_URL" \
  --job-id "$JOB_NAME" \
  --token "$JENKINS_TOKEN" \
  --username "$JENKINS_USER" \
  --build "$BUILD_NUMBER" \
  --save jenkins-test.log

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to fetch logs${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check if Jenkins is running: curl $JENKINS_URL"
    echo "2. Verify token: curl -u $JENKINS_USER:TOKEN $JENKINS_URL/api/json"
    echo "3. Check job name: curl -u $JENKINS_USER:TOKEN $JENKINS_URL/api/json?tree=jobs[name]"
    exit 1
fi

# Step 2: Analyze fetched logs
echo ""
echo -e "${YELLOW}🔍 Step 2: Analyzing fetched logs...${NC}"
echo ""

python -m src.cli analyze jenkins-test.log

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Analysis completed successfully!${NC}"
    echo ""
    echo "📁 Log saved to: jenkins-test.log"
    echo ""
    echo "Try these commands:"
    echo "  • View summary: python -m src.cli summarize jenkins-test.log"
    echo "  • JSON output:  python -m src.cli analyze jenkins-test.log --format json"
    echo "  • Full details: python -m src.cli analyze jenkins-test.log --full"
else
    echo -e "${RED}❌ Analysis failed${NC}"
    exit 1
fi
