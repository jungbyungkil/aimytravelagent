#!/bin/bash

# ============================================
# Travel AI Agent - EC2 자동 배포 스크립트
# ============================================

set -e  # 오류 발생 시 즉시 중단

echo "========================================================================"
echo "✈️  Travel AI Agent - EC2 자동 배포"
echo "========================================================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 시스템 확인
echo "📋 1단계: 시스템 확인 중..."
echo "----------------------------------------"

# OS 확인
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "OS: $NAME $VERSION"
else
    echo "❌ OS를 확인할 수 없습니다."
    exit 1
fi

# Python 버전 확인
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
    echo "✅ Python: $(python3.11 --version)"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    echo "⚠️  Python: $(python3 --version)"
    echo "   (Python 3.11+ 권장)"
else
    echo "❌ Python이 설치되어 있지 않습니다."
    echo "   설치: sudo yum install python3.11 -y"
    exit 1
fi

# Git 확인
if command -v git &> /dev/null; then
    echo "✅ Git: $(git --version)"
else
    echo "❌ Git이 설치되어 있지 않습니다."
    echo "   설치: sudo yum install git -y"
    exit 1
fi

echo ""

# 2. 프로젝트 디렉토리 확인
echo "📁 2단계: 프로젝트 디렉토리 설정"
echo "----------------------------------------"

PROJECT_DIR="$HOME/travel-agent"

if [ -d "$PROJECT_DIR" ]; then
    echo "✅ 프로젝트 디렉토리 존재: $PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # Git 업데이트
    if [ -d .git ]; then
        echo "🔄 Git 업데이트 중..."
        git pull origin main || git pull origin master || echo "⚠️  업데이트 실패 (수동 확인 필요)"
    fi
else
    echo "⚠️  프로젝트 디렉토리가 없습니다."
    echo "📥 GitHub에서 클론하시겠습니까? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "GitHub 저장소 URL을 입력하세요:"
        read -r repo_url
        
        git clone "$repo_url" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
        echo "✅ 클론 완료"
    else
        echo "❌ 프로젝트 디렉토리를 찾을 수 없습니다."
        exit 1
    fi
fi

echo ""

# 3. 가상환경 설정
echo "🔧 3단계: 가상환경 설정"
echo "----------------------------------------"

if [ ! -d "venv" ]; then
    echo "📦 가상환경 생성 중..."
    $PYTHON_CMD -m venv venv
    echo "✅ 가상환경 생성 완료"
else
    echo "✅ 가상환경 이미 존재"
fi

# 가상환경 활성화
source venv/bin/activate
echo "✅ 가상환경 활성화: $(which python)"

echo ""

# 4. 라이브러리 설치
echo "📦 4단계: 라이브러리 설치"
echo "----------------------------------------"

if [ -f "requirements.txt" ]; then
    echo "📥 requirements.txt에서 설치 중..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ 라이브러리 설치 완료"
else
    echo "❌ requirements.txt를 찾을 수 없습니다."
    exit 1
fi

echo ""

# 5. 환경 변수 확인
echo "⚙️  5단계: 환경 변수 확인"
echo "----------------------------------------"

if [ -f ".env" ]; then
    echo "✅ .env 파일 존재"
    
    # API 키 확인
    if grep -q "OPENAI_API_KEY=sk-" .env; then
        echo "✅ OpenAI API 키 설정됨"
    else
        echo -e "${YELLOW}⚠️  OpenAI API 키가 설정되지 않았을 수 있습니다.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  .env 파일이 없습니다.${NC}"
    
    if [ -f ".env.example" ]; then
        echo "📝 .env.example에서 복사하시겠습니까? (y/n)"
        read -r response
        
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            cp .env.example .env
            echo "✅ .env 파일 생성됨"
            echo "⚠️  nano .env 명령으로 API 키를 입력해주세요!"
        fi
    else
        echo "📝 .env 파일을 생성합니다..."
        cat > .env << 'EOF'
# OpenAI API Key
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o
EOF
        echo "✅ .env 파일 생성됨"
        echo -e "${YELLOW}⚠️  nano .env 명령으로 API 키를 입력해주세요!${NC}"
    fi
fi

echo ""

# 6. 필요한 폴더 생성
echo "📂 6단계: 필요한 폴더 생성"
echo "----------------------------------------"

mkdir -p bookings output

echo "✅ bookings/ 폴더"
echo "✅ output/ 폴더"

# bookings 폴더 파일 확인
file_count=$(ls -1 bookings/*.{txt,pdf} 2>/dev/null | wc -l)
if [ "$file_count" -gt 0 ]; then
    echo "✅ bookings/ 폴더에 $file_count 개의 파일 존재"
else
    echo -e "${YELLOW}⚠️  bookings/ 폴더가 비어있습니다.${NC}"
    echo "   예약 파일을 업로드해주세요."
fi

echo ""

# 7. 설치 확인
echo "🔍 7단계: 설치 확인"
echo "----------------------------------------"

echo "필수 패키지 확인:"
python -c "
import sys
packages = {
    'openai': 'OpenAI API',
    'dotenv': '환경 변수',
    'pydantic': '데이터 검증',
    'PyPDF2': 'PDF 처리',
    'icalendar': '캘린더',
    'dateutil': '날짜 처리'
}

all_ok = True
for package, desc in packages.items():
    try:
        __import__(package)
        print(f'✅ {desc:20} ({package})')
    except ImportError:
        print(f'❌ {desc:20} ({package})')
        all_ok = False

sys.exit(0 if all_ok else 1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 모든 필수 패키지 설치 완료!${NC}"
else
    echo ""
    echo -e "${RED}❌ 일부 패키지가 설치되지 않았습니다.${NC}"
    echo "   pip install -r requirements.txt 를 다시 실행해주세요."
    exit 1
fi

echo ""

# 8. 완료
echo "========================================================================"
echo -e "${GREEN}✅ 배포 완료!${NC}"
echo "========================================================================"
echo ""
echo "다음 단계:"
echo "1. .env 파일 확인 및 API 키 입력:"
echo "   nano .env"
echo ""
echo "2. 예약 파일 업로드 (로컬에서):"
echo "   scp -i key.pem booking.txt ec2-user@$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):~/travel-agent/bookings/"
echo ""
echo "3. 프로그램 실행:"
echo "   source ~/travel-agent/venv/bin/activate"
echo "   cd ~/travel-agent"
echo "   python ultimate_travel_agent.py"
echo ""
echo "4. 백그라운드 실행:"
echo "   tmux new -s travel-agent"
echo "   python ultimate_travel_agent.py"
echo "   # Ctrl+B, D 로 세션에서 나오기"
echo ""
echo "🚀 즐거운 여행 되세요!"
echo ""