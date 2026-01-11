"""
Travel AI Agent - 자동 설치 스크립트
모든 필수 라이브러리를 자동으로 설치합니다.
"""

import subprocess
import sys
import os

def install_requirements():
    """requirements.txt의 모든 패키지 설치"""
    print("=" * 70)
    print("✈️  Travel AI Agent - 라이브러리 설치")
    print("=" * 70)
    print()
    
    # requirements.txt 존재 확인
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt 파일을 찾을 수 없습니다.")
        return False
    
    print("📦 필수 라이브러리 설치 시작...\n")
    
    try:
        # pip 업그레이드
        print("1️⃣ pip 업그레이드 중...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
        ])
        print("✅ pip 업그레이드 완료\n")
        
        # requirements.txt 설치
        print("2️⃣ 필수 패키지 설치 중...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("\n✅ 모든 패키지 설치 완료!\n")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 설치 중 오류 발생: {e}")
        return False

def verify_installation():
    """설치된 패키지 확인"""
    print("=" * 70)
    print("🔍 설치 확인")
    print("=" * 70)
    print()
    
    required_packages = {
        'openai': 'OpenAI API',
        'dotenv': '환경 변수 관리',
        'pydantic': '데이터 검증',
        'PyPDF2': 'PDF 처리',
        'icalendar': '캘린더 파일 생성',
        'dateutil': '날짜 처리',
        'google.auth': 'Google 인증',
        'googleapiclient': 'Google Calendar API'
    }
    
    print("설치된 패키지 확인:\n")
    
    all_installed = True
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {description:30} ({package})")
        except ImportError:
            if package in ['google.auth', 'googleapiclient']:
                print(f"⚠️  {description:30} ({package}) - 선택사항")
            else:
                print(f"❌ {description:30} ({package}) - 설치 필요")
                all_installed = False
    
    print()
    
    if all_installed:
        print("🎉 모든 필수 패키지가 정상적으로 설치되었습니다!")
    else:
        print("⚠️  일부 패키지가 설치되지 않았습니다.")
    
    print()
    return all_installed

def create_env_template():
    """환경 변수 템플릿 생성"""
    if os.path.exists('.env'):
        print("ℹ️  .env 파일이 이미 존재합니다. 건너뜁니다.\n")
        return
    
    env_template = """# OpenAI API Key
# https://platform.openai.com/api-keys 에서 발급
OPENAI_API_KEY=your-openai-api-key-here

# 선택사항: OpenAI 모델 설정
# OPENAI_MODEL=gpt-4o
"""
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_template)
    
    print("📝 .env.example 파일이 생성되었습니다.")
    print("   이 파일을 .env로 복사하고 API 키를 입력하세요.\n")

def create_folders():
    """필요한 폴더 생성"""
    folders = ['bookings', 'output']
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"📁 {folder}/ 폴더 생성")
    
    print()

def main():
    """메인 실행"""
    print()
    
    # 1. 라이브러리 설치
    if not install_requirements():
        print("설치를 다시 시도하거나 수동으로 설치해주세요:")
        print("pip install -r requirements.txt")
        return
    
    # 2. 설치 확인
    verify_installation()
    
    # 3. 환경 설정 파일 생성
    print("=" * 70)
    print("⚙️  초기 설정")
    print("=" * 70)
    print()
    
    create_env_template()
    create_folders()
    
    # 4. 완료 메시지
    print("=" * 70)
    print("✅ 설치 완료!")
    print("=" * 70)
    print()
    print("다음 단계:")
    print("1. .env.example 파일을 .env로 복사")
    print("2. .env 파일에 OpenAI API 키 입력")
    print("3. bookings/ 폴더에 예약 파일 넣기")
    print("4. python ultimate_travel_agent.py 실행")
    print()
    print("🚀 즐거운 여행 되세요!")
    print()

if __name__ == "__main__":
    main()