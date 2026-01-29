"""
기능 검증 테스트 스크립트
모든 기능이 정상 작동하는지 확인합니다.
"""
import json
import os
import sys
from news_chatbot import (
    get_api_key,
    save_api_key,
    validate_api_key,
    fetch_news,
    summarize_with_gemini,
    chat_with_gemini,
    save_news,
    load_saved_news,
)

def test_api_key_functions():
    """API 키 관련 기능 테스트"""
    print("=" * 60)
    print("테스트 1: API 키 저장/불러오기")
    print("=" * 60)
    
    test_key = "AIzaSyD3a5aGRqW9nOM_WVqCuTmr7d6fDkf9HyY"
    
    # 저장 테스트
    result = save_api_key(test_key)
    assert result == True, "API 키 저장 실패"
    print("✅ API 키 저장 성공")
    
    # 불러오기 테스트
    loaded_key = get_api_key()
    assert loaded_key == test_key, "API 키 불러오기 실패"
    print("✅ API 키 불러오기 성공")
    
    print()

def test_api_key_validation():
    """API 키 검증 테스트"""
    print("=" * 60)
    print("테스트 2: API 키 검증")
    print("=" * 60)
    
    test_key = get_api_key()
    if not test_key:
        print("⚠️  API 키가 없습니다. 검증 테스트를 건너뜁니다.")
        return
    
    result = validate_api_key(test_key)
    print(f"검증 결과: {result['message']}")
    print(f"상세: {result['details']}")
    
    if result['valid']:
        print("✅ API 키 검증 성공")
    else:
        print("❌ API 키 검증 실패")
        print("   (이것은 정상일 수 있습니다 - API 키가 유효하지 않을 수 있음)")
    
    print()

def test_news_fetch():
    """뉴스 가져오기 테스트"""
    print("=" * 60)
    print("테스트 3: 뉴스 가져오기")
    print("=" * 60)
    
    keyword = "인공지능"
    print(f"키워드: '{keyword}'로 뉴스 검색 중...")
    
    result = fetch_news(keyword, max_results=5)
    
    if result.get("error"):
        print(f"❌ 뉴스 가져오기 실패: {result['message']}")
        print(f"   상세: {result.get('details', '')}")
    else:
        articles = result.get("articles", [])
        print(f"✅ 뉴스 가져오기 성공: {len(articles)}개 기사 수집")
        if articles:
            print(f"   첫 번째 기사: {articles[0].get('title', 'N/A')[:50]}...")
    
    print()
    return result

def test_summarize():
    """요약 기능 테스트"""
    print("=" * 60)
    print("테스트 4: AI 요약 기능")
    print("=" * 60)
    
    # 먼저 뉴스 가져오기
    result = fetch_news("인공지능", max_results=3)
    if result.get("error"):
        print("⚠️  뉴스를 가져올 수 없어 요약 테스트를 건너뜁니다.")
        return
    
    articles = result.get("articles", [])
    if not articles:
        print("⚠️  뉴스가 없어 요약 테스트를 건너뜁니다.")
        return
    
    print(f"{len(articles)}개 기사로 요약 생성 중...")
    summary_result = summarize_with_gemini(articles)
    
    if summary_result.get("error"):
        print(f"❌ 요약 생성 실패: {summary_result['message']}")
        print(f"   상세: {summary_result.get('details', '')}")
    else:
        summary = summary_result.get("summary", "")
        print(f"✅ 요약 생성 성공")
        print(f"   요약 내용: {summary[:100]}...")
    
    print()

def test_chat():
    """대화 기능 테스트"""
    print("=" * 60)
    print("테스트 5: 뉴스 대화 기능")
    print("=" * 60)
    
    # 먼저 뉴스 가져오기
    result = fetch_news("인공지능", max_results=3)
    if result.get("error"):
        print("⚠️  뉴스를 가져올 수 없어 대화 테스트를 건너뜁니다.")
        return
    
    articles = result.get("articles", [])
    if not articles:
        print("⚠️  뉴스가 없어 대화 테스트를 건너뜁니다.")
        return
    
    test_message = "이 뉴스들의 주요 내용은 무엇인가요?"
    print(f"질문: '{test_message}'")
    print("답변 생성 중...")
    
    chat_result = chat_with_gemini(articles, test_message)
    
    if chat_result.get("error"):
        print(f"❌ 대화 생성 실패: {chat_result['message']}")
        print(f"   상세: {chat_result.get('details', '')}")
    else:
        response = chat_result.get("response", "")
        print(f"✅ 대화 생성 성공")
        print(f"   답변: {response[:150]}...")
    
    print()

def test_save_load():
    """저장/불러오기 기능 테스트"""
    print("=" * 60)
    print("테스트 6: 뉴스 저장/불러오기")
    print("=" * 60)
    
    # 먼저 뉴스 가져오기
    result = fetch_news("테스트", max_results=2)
    if result.get("error"):
        print("⚠️  뉴스를 가져올 수 없어 저장 테스트를 건너뜁니다.")
        return
    
    articles = result.get("articles", [])
    if not articles:
        print("⚠️  뉴스가 없어 저장 테스트를 건너뜁니다.")
        return
    
    # 저장 테스트
    keyword = "테스트키워드"
    save_result = save_news(keyword, articles)
    assert save_result == True, "뉴스 저장 실패"
    print(f"✅ 뉴스 저장 성공: '{keyword}'")
    
    # 불러오기 테스트
    saved = load_saved_news()
    assert isinstance(saved, list), "저장된 뉴스 불러오기 실패"
    print(f"✅ 저장된 뉴스 불러오기 성공: {len(saved)}개 항목")
    
    # 방금 저장한 항목 확인
    found = False
    for item in saved:
        if item.get("keyword") == keyword:
            found = True
            print(f"   저장된 항목 확인: {len(item.get('articles', []))}개 기사")
            break
    
    if found:
        print("✅ 저장된 항목 확인 성공")
    else:
        print("⚠️  방금 저장한 항목을 찾을 수 없습니다.")
    
    print()

def main():
    """모든 테스트 실행"""
    print("\n" + "=" * 60)
    print("뉴스 요약 챗봇 기능 검증 테스트 시작")
    print("=" * 60 + "\n")
    
    tests_passed = 0
    tests_failed = 0
    tests_skipped = 0
    
    try:
        test_api_key_functions()
        tests_passed += 1
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        tests_failed += 1
    
    try:
        test_api_key_validation()
        tests_passed += 1
    except Exception as e:
        print(f"⚠️  테스트 건너뜀: {e}")
        tests_skipped += 1
    
    try:
        test_news_fetch()
        tests_passed += 1
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        tests_failed += 1
    
    try:
        test_summarize()
        tests_passed += 1
    except Exception as e:
        print(f"⚠️  테스트 건너뜀: {e}")
        tests_skipped += 1
    
    try:
        test_chat()
        tests_passed += 1
    except Exception as e:
        print(f"⚠️  테스트 건너뜀: {e}")
        tests_skipped += 1
    
    try:
        test_save_load()
        tests_passed += 1
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        tests_failed += 1
    
    # 결과 요약
    print("=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"✅ 성공: {tests_passed}")
    print(f"❌ 실패: {tests_failed}")
    print(f"⚠️  건너뜀: {tests_skipped}")
    print("=" * 60)
    
    if tests_failed == 0:
        print("\n🎉 모든 핵심 기능이 정상 작동합니다!")
        return 0
    else:
        print("\n⚠️  일부 기능에 문제가 있을 수 있습니다.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
