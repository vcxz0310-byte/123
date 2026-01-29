import json
import os
import textwrap
import urllib.parse
from datetime import datetime

import feedparser
import google.generativeai as genai
import requests


GOOGLE_NEWS_SEARCH_RSS = (
    "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
)

# API 키 저장 파일 경로
API_KEY_FILE = "api_key.json"
SAVED_NEWS_FILE = "saved_news.json"


def get_api_key():
    """저장된 API 키를 불러옵니다."""
    try:
        if os.path.exists(API_KEY_FILE):
            with open(API_KEY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("api_key", "")
        return ""
    except Exception:
        return ""


def save_api_key(api_key: str):
    """API 키를 저장합니다."""
    try:
        with open(API_KEY_FILE, "w", encoding="utf-8") as f:
            json.dump({"api_key": api_key}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def validate_api_key(api_key: str) -> dict:
    """API 키 유효성을 검증합니다."""
    if not api_key or not api_key.strip():
        return {
            "valid": False,
            "message": "❌ API 키가 입력되지 않았습니다.",
            "details": "재미나이(Gemini) API 키를 입력해주세요."
        }
    
    api_key = api_key.strip()
    
    # 기본 형식 검증
    if not api_key.startswith("AIza"):
        return {
            "valid": False,
            "message": "❌ API 키 형식이 올바르지 않습니다.",
            "details": "재미나이 API 키는 'AIza'로 시작해야 합니다."
        }
    
    # 실제 API 호출로 검증
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        # 간단한 테스트 요청
        response = model.generate_content("테스트")
        if response:
            return {
                "valid": True,
                "message": "✅ API 키가 유효합니다! 정상적으로 작동합니다.",
                "details": f"API 키 검증 성공. 모델 응답 확인 완료."
            }
    except Exception as e:
        error_str = str(e)
        if "API_KEY_INVALID" in error_str or "invalid" in error_str.lower():
            return {
                "valid": False,
                "message": "❌ API 키가 유효하지 않습니다.",
                "details": f"오류 내용: {error_str}\n\n올바른 API 키를 입력해주세요."
            }
        elif "quota" in error_str.lower() or "limit" in error_str.lower():
            return {
                "valid": False,
                "message": "⚠️ API 키는 유효하지만 사용량 한도에 도달했습니다.",
                "details": f"오류 내용: {error_str}\n\nAPI 사용량을 확인해주세요."
            }
        else:
            return {
                "valid": False,
                "message": "❌ API 키 검증 중 오류가 발생했습니다.",
                "details": f"오류 내용: {error_str}\n\n네트워크 연결을 확인하거나 잠시 후 다시 시도해주세요."
            }
    
    return {
        "valid": False,
        "message": "❌ API 키 검증에 실패했습니다.",
        "details": "알 수 없는 오류가 발생했습니다."
    }


def fetch_news(keyword: str, max_results: int = 10):
    """Fetch news from Google News RSS for the given keyword."""
    query = urllib.parse.quote(keyword)
    url = GOOGLE_NEWS_SEARCH_RSS.format(query=query)

    try:
        # Use requests so we can handle HTTP errors explicitly
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        return {
            "error": True,
            "message": "네트워크 요청 시간이 초과되었습니다.",
            "details": "인터넷 연결을 확인하거나 잠시 후 다시 시도해주세요."
        }
    except requests.exceptions.ConnectionError:
        return {
            "error": True,
            "message": "인터넷 연결에 실패했습니다.",
            "details": "인터넷 연결 상태를 확인해주세요."
        }
    except requests.RequestException as e:
        return {
            "error": True,
            "message": f"뉴스를 불러오는 중 오류가 발생했습니다: {str(e)}",
            "details": "네트워크 연결을 확인하거나 잠시 후 다시 시도해주세요."
        }

    try:
        feed = feedparser.parse(resp.content)
    except Exception as e:
        return {
            "error": True,
            "message": "뉴스 데이터를 파싱하는 중 오류가 발생했습니다.",
            "details": str(e)
        }

    articles = []
    for entry in feed.entries[:max_results]:
        title = entry.get("title", "(제목 없음)")
        link = entry.get("link", "")
        summary = entry.get("summary", "") or entry.get("description", "")
        published = entry.get("published", "")

        # Try to parse date to a nicer format
        published_str = published
        if published:
            try:
                # feedparser returns a structured time in published_parsed
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    dt = datetime(*entry.published_parsed[:6])
                    published_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                # Fallback to raw string
                published_str = published

        articles.append(
            {
                "title": title,
                "link": link,
                "summary": summary,
                "published": published_str,
            }
        )

    return {"error": False, "articles": articles}


def summarize_with_gemini(articles: list) -> dict:
    """재미나이 API를 사용하여 뉴스 기사들을 요약합니다."""
    api_key = get_api_key()
    if not api_key:
        return {
            "error": True,
            "message": "API 키가 설정되지 않았습니다.",
            "details": "상단에서 재미나이 API 키를 입력하고 검증해주세요."
        }

    if not articles:
        return {
            "error": True,
            "message": "요약할 뉴스가 없습니다."
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # 뉴스 기사들을 텍스트로 정리
        news_text = "다음은 수집한 뉴스 기사들입니다:\n\n"
        for idx, article in enumerate(articles, 1):
            title = article.get("title", "")
            summary = article.get("summary", "")
            news_text += f"[기사 {idx}]\n제목: {title}\n내용: {summary}\n\n"

        prompt = f"""다음 뉴스 기사들을 읽고 전체적인 요약을 한국어로 작성해주세요.
요약은 3-5문장 정도로 간결하게 작성하고, 주요 내용과 핵심 포인트를 포함해주세요.

{news_text}

요약:"""

        response = model.generate_content(prompt)
        return {
            "error": False,
            "summary": response.text.strip()
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"요약 생성 중 오류가 발생했습니다: {str(e)}",
            "details": "API 키가 유효한지 확인하거나 잠시 후 다시 시도해주세요."
        }


def chat_with_gemini(articles: list, user_message: str) -> dict:
    """재미나이 API를 사용하여 수집한 뉴스 기사들에 대해 대화합니다."""
    api_key = get_api_key()
    if not api_key:
        return {
            "error": True,
            "message": "API 키가 설정되지 않았습니다.",
            "details": "상단에서 재미나이 API 키를 입력하고 검증해주세요."
        }

    if not articles:
        return {
            "error": True,
            "message": "대화할 뉴스가 없습니다. 먼저 뉴스를 검색해주세요."
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # 뉴스 기사들을 텍스트로 정리
        news_text = "다음은 수집한 뉴스 기사들입니다:\n\n"
        for idx, article in enumerate(articles, 1):
            title = article.get("title", "")
            summary = article.get("summary", "")
            published = article.get("published", "")
            news_text += f"[기사 {idx}]\n제목: {title}\n발행일: {published}\n내용: {summary}\n\n"

        prompt = f"""당신은 뉴스 분석 전문가입니다. 사용자가 제공한 뉴스 기사들을 바탕으로 질문에 답변해주세요.
뉴스 기사 내용을 참고하여 정확하고 도움이 되는 답변을 한국어로 작성해주세요.

{news_text}

사용자 질문: {user_message}

답변:"""

        response = model.generate_content(prompt)
        return {
            "error": False,
            "response": response.text.strip()
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"대화 생성 중 오류가 발생했습니다: {str(e)}",
            "details": "API 키가 유효한지 확인하거나 잠시 후 다시 시도해주세요."
        }


def save_news(keyword: str, articles: list):
    """키워드와 뉴스 기사들을 JSON 파일에 저장합니다."""
    try:
        # 기존 데이터 불러오기
        if os.path.exists(SAVED_NEWS_FILE):
            with open(SAVED_NEWS_FILE, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
        else:
            saved_data = []

        # 새 데이터 추가
        saved_data.append(
            {
                "keyword": keyword,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "articles": articles,
            }
        )

        # 저장
        with open(SAVED_NEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(saved_data, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"저장 중 오류 발생: {e}")
        return False


def load_saved_news():
    """저장된 뉴스 데이터를 불러옵니다."""
    try:
        if os.path.exists(SAVED_NEWS_FILE):
            with open(SAVED_NEWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"불러오기 중 오류 발생: {e}")
        return []


def simple_summarize(text: str, max_sentences: int = 2) -> str:
    """Very simple summarizer: take the first N 'sentences'."""
    if not text:
        return "(요약할 내용이 없습니다.)"

    # Replace HTML breaks that sometimes appear in RSS
    cleaned = (
        text.replace("<br>", ". ")
        .replace("<br/>", ". ")
        .replace("<br />", ". ")
        .replace("&nbsp;", " ")
    )

    # Split by typical Korean / English sentence delimiters
    # This is very naive but usually good enough.
    sentences = []
    current = ""
    for ch in cleaned:
        current += ch
        if ch in ".?!？！" or ch == "다" or ch == "요":
            # Heuristic: treat some endings as sentence boundaries
            if current.strip():
                sentences.append(current.strip())
                current = ""
    if current.strip():
        sentences.append(current.strip())

    if not sentences:
        return cleaned.strip()

    summary = " ".join(sentences[:max_sentences])
    return summary.strip()


def print_articles(articles):
    if not articles:
        print("관련 뉴스를 찾지 못했습니다.")
        return

    for idx, article in enumerate(articles, start=1):
        print("=" * 80)
        print(f"[{idx}] {article['title']}")
        if article.get("published"):
            print(f" - 날짜: {article['published']}")

        short = simple_summarize(article.get("summary", ""))
        print()
        print(textwrap.fill(short, width=80))
        if article.get("link"):
            print()
            print(f"링크: {article['link']}")
    print("=" * 80)


def chat_loop():
    print("=== 뉴스 요약 챗봇 ===")
    print("키워드를 입력하면 구글 뉴스에서 관련 기사를 10개 찾아 요약해 드립니다.")
    print("종료하려면 'quit' 또는 'exit' 을(를) 입력하세요.\n")

    while True:
        keyword = input("검색할 키워드: ").strip()
        if not keyword:
            continue

        if keyword.lower() in {"quit", "exit", "종료", "끝"}:
            print("챗봇을 종료합니다. 이용해 주셔서 감사합니다.")
            break

        print(f"\n'{keyword}' 관련 뉴스를 검색 중입니다...\n")
        result = fetch_news(keyword, max_results=10)
        if result.get("error"):
            print(f"오류: {result.get('message')}")
        else:
            print_articles(result.get("articles", []))
        print()


if __name__ == "__main__":
    chat_loop()
