import os
import subprocess
import requests # 글을 가져올 때
from bs4 import BeautifulSoup # HTML 파싱
import html2text # Markdown 변환

# GitHub Actions 환경에서 실행될 때 저장소의 루트 경로
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(REPO_ROOT, "posts") # Markdown 파일이 저장될 폴더 (예: tech_blog/posts)

# 폴더가 없으면 생성 (최초 실행 시 필요)
if not os.path.exists(POSTS_DIR):
    os.makedirs(POSTS_DIR)

def fetch_tistory_posts():
    """
    티스토리에서 모든 게시글의 제목, 내용(HTML), 고유 ID를 가져오는 함수입니다.
    (실제 API 호출이나 XML 파싱 로직이 들어가야 합니다.)
    """
    # 임시 데이터 (실제 데이터로 대체해야 함)
    posts_data = [
        {
            "id": 1,
            "title": "자동화 스크립트 첫 글",
            "html_content": "<h1>티스토리 첫 글입니다.</h1><p>내용이 조금 바뀌었어요!</p>",
            "modified_date": "2025-11-18 10:00:00" # 변경 감지를 위한 메타데이터
        },
        # ... 다른 글들 ...
    ]
    return posts_data


def check_and_update_posts(posts_data):
    """글을 Markdown으로 변환하고, 변경 사항이 있으면 파일에 저장합니다."""

    changes_detected = False
    converter = html2text.HTML2Text()
    converter.skip_internal_links = True
    converter.body_width = 0  # 줄바꿈 방지

    for post in posts_data:
        # 1. HTML을 Markdown으로 변환
        markdown_content = converter.handle(post["html_content"])

        # 2. 파일 이름 설정
        filename = os.path.join(POSTS_DIR, f"{post['id']}_{post['title']}.md")

        # 3. 기존 파일 내용 읽기
        existing_content = ""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_content = f.read()

        # 4. 내용 비교 (변경 감지)
        if existing_content != markdown_content:
            print(f"✅ 변경 감지됨: {post['title']}")

            # 5. 파일 덮어쓰기
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {post['title']}\n\n")  # 제목을 Markdown 헤더로 추가
                f.write(markdown_content)

            changes_detected = True  # 변경 플래그 설정
        # else:
        # print(f"➖ 변경 없음: {post['title']}")

    return changes_detected


def commit_and_push(changes_detected):
    """Git 명령어를 실행하여 변경 사항을 커밋하고 푸시합니다."""

    if not changes_detected:
        print("변경 사항이 없어 Git 작업을 건너뜁니다.")
        return

    try:
        # 모든 변경된 파일 스테이징
        subprocess.run(["git", "add", "."], check=True)

        # 커밋 메시지 설정
        commit_message = "Auto-sync: Updated Tistory posts"

        # 커밋 실행
        # check=True: 명령 실행 실패 시 예외 발생
        subprocess.run(["git", "commit", "-m", commit_message], check=True)

        # ------------------------------------------------------------------
        # 🚨 [여기부터 아래 5줄이 새롭게 추가되거나 수정되어야 하는 부분입니다] 🚨
        # 푸시 실행: 토큰을 사용하여 인증합니다.
        
        # GitHub Actions 환경 변수 가져오기
        token = os.environ.get('GITHUB_TOKEN')
        repo_name = os.environ.get('GITHUB_REPOSITORY') 
        
        # 인증 정보를 포함한 Git Push URL을 만듭니다.
        repo_url = f"https://x-access-token:{token}@github.com/{repo_name}.git"

        # 푸시 실행 (일반적인 git push 대신 토큰 URL로 푸시)
        subprocess.run(["git", "push", repo_url], check=True)
        
        # ------------------------------------------------------------------

        print("🎉 Git 커밋 및 푸시 성공!")

    except subprocess.CalledProcessError as e:
        # ... (예외 처리 부분은 그대로 유지합니다)
        print(f"⚠️ Git 작업 실패: {e}")


if __name__ == "__main__":
    print("--- 티스토리 자동 연동 스크립트 시작 ---")

    # 1. 글 데이터 가져오기
    posts_data = fetch_tistory_posts()

    # 2. 변경 확인 및 파일 업데이트
    was_changed = check_and_update_posts(posts_data)

    # 3. 변경 사항이 있으면 Git 작업 실행
    commit_and_push(was_changed)


    print("--- 스크립트 종료 ---")
