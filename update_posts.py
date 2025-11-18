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
    """Tistory Open API를 사용하여 모든 게시글을 가져옵니다."""
    
    # 1. API 인증 정보 및 설정 불러오기
    # GitHub Secrets에 저장한 환경 변수를 사용합니다.
    ACCESS_TOKEN = os.environ.get("TISTORY_ACCESS_TOKEN")
    BLOG_NAME = os.environ.get("TISTORY_BLOG_NAME")
    
    if not ACCESS_TOKEN or not BLOG_NAME:
        print("🚨 오류: TISTORY_ACCESS_TOKEN 또는 BLOG_NAME이 설정되지 않았습니다.")
        # 실패하더라도 빈 리스트를 반환하여 스크립트가 중단되지 않게 처리
        return []

    url = "https://www.tistory.com/apis/post/list"
    all_posts = []
    page = 1
    
    print(f"📡 {BLOG_NAME} 블로그에서 게시글 목록을 가져오는 중...")

    while True:
        params = {
            'access_token': ACCESS_TOKEN,
            'output': 'json',
            'blogName': BLOG_NAME,
            'page': page
            # 'count' 파라미터를 사용해 한 번에 가져올 개수(최대 100)를 설정할 수 있습니다.
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status() # HTTP 오류 발생 시 예외 발생
            data = response.json()
            
            # API 응답 구조 확인 및 오류 처리
            if data.get('tistory', {}).get('status') != '200':
                print(f"🚨 API 오류: {data.get('tistory', {}).get('message')}")
                break
                
            posts_info = data['tistory']['item']['posts']
            total_count = int(data['tistory']['item']['totalCount'])
            
            # 2. 필요한 데이터 추출 및 형식 변환
            for post in posts_info:
                # post/read API를 호출하여 글 내용을 가져와야 합니다.
                # (목록 API는 내용을 제공하지 않습니다.)
                
                # 하지만 이 단계에서는 간단히 목록 데이터만 사용해봅시다.
                # 글의 내용을 가져오는 함수를 따로 작성해야 하지만, 여기서는 임시로
                # 'post/read'를 호출해야 한다고 가정합니다.
                
                # --- [post/read API 호출 로직이 필요함] ---
                
                # 글 내용을 가져왔다고 가정하고 리스트에 추가합니다.
                # 실제 글을 읽어오는 로직은 이 함수 내에서 다시 호출되거나, 
                # posts_data를 만든 후 글 내용만 업데이트하는 방식으로 구현할 수 있습니다.
                
                # 임시로 제목과 ID만 사용하며, 내용은 비워둡니다. 
                # 사용자님의 check_and_update_posts 함수가 HTML 내용을 사용하므로, 
                # 반드시 post/read API를 호출해 내용을 채워야 합니다.
                
                # 일단 ID와 제목, 수정일만 추출
                all_posts.append({
                    "id": post['id'],
                    "title": post['title'],
                    "html_content": "", # ⚠️ 이 부분은 반드시 post/read API로 채워야 합니다!
                    "modified_date": post['postUrl'].split('/')[-1] # 예시
                })

            # 3. 페이지네이션 처리
            if len(all_posts) >= total_count:
                break # 모든 글을 가져왔다면 루프 종료
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"🚨 네트워크 오류 발생: {e}")
            break
            
    # 4. (필수) all_posts의 'html_content'를 채우기 위해 
    #    각 게시글별로 Tistory post/read API를 호출하는 로직이 추가되어야 합니다.
    #    이 과정이 가장 복잡하며, 모든 글의 본문(content)을 가져와야 합니다.
    
    return all_posts


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

