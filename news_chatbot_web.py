from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

from news_chatbot import (
    fetch_news,
    summarize_with_gemini,
    chat_with_gemini,
    save_news,
    load_saved_news,
    get_api_key,
    save_api_key,
    validate_api_key,
)


app = Flask(__name__)
CORS(app)  # file:// 에서도 localhost API 호출 가능


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>뉴스 요약 챗봇</title>
  <link
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
    rel="stylesheet"
    integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH"
    crossorigin="anonymous"
  />
  <style>
    body {
      background-color: #f5f5f7;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main-container {
      max-width: 1400px;
      margin: 20px auto;
      padding: 0 20px;
    }
    .section-card {
      background: #ffffff;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      padding: 24px;
      margin-bottom: 20px;
    }
    .section-title {
      font-size: 1.25rem;
      font-weight: 600;
      margin-bottom: 16px;
      color: #111827;
      border-bottom: 2px solid #3b82f6;
      padding-bottom: 8px;
    }
    .api-key-input {
      font-family: monospace;
      font-size: 0.95rem;
    }
    .validation-result {
      padding: 12px;
      border-radius: 8px;
      margin-top: 12px;
      font-size: 0.95rem;
    }
    .validation-success {
      background-color: #d1fae5;
      border: 1px solid #10b981;
      color: #065f46;
    }
    .validation-error {
      background-color: #fee2e2;
      border: 1px solid #ef4444;
      color: #991b1b;
    }
    .validation-warning {
      background-color: #fef3c7;
      border: 1px solid #f59e0b;
      color: #92400e;
    }
    .article-card {
      border-radius: 8px;
      border: 1px solid #e5e7eb;
      padding: 14px;
      margin-bottom: 10px;
      background-color: #f9fafb;
    }
    .article-title {
      font-size: 0.95rem;
      font-weight: 600;
      margin-bottom: 4px;
    }
    .article-meta {
      font-size: 0.85rem;
      color: #6b7280;
      margin-bottom: 6px;
    }
    .article-summary {
      font-size: 0.9rem;
      color: #111827;
    }
    .chat-container {
      min-height: 400px;
      max-height: 500px;
      overflow-y: auto;
      border: 2px solid #3b82f6;
      border-radius: 8px;
      padding: 16px;
      background-color: #ffffff;
      margin-bottom: 12px;
    }
    .message {
      margin-bottom: 12px;
      padding: 12px 14px;
      border-radius: 8px;
      word-wrap: break-word;
      line-height: 1.6;
    }
    .message.user {
      background-color: #3b82f6;
      color: white;
      margin-left: 20%;
      text-align: right;
    }
    .message.bot {
      background-color: #f3f4f6;
      color: #111827;
      margin-right: 20%;
      border: 1px solid #e5e7eb;
    }
    .summary-box {
      background-color: #eff6ff;
      border-left: 4px solid #3b82f6;
      padding: 16px;
      border-radius: 8px;
      margin-bottom: 16px;
    }
    .grid-layout {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    @media (max-width: 1200px) {
      .grid-layout {
        grid-template-columns: 1fr;
      }
    }
    .status-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 0.85rem;
      font-weight: 500;
      margin-left: 8px;
    }
    .status-ready {
      background-color: #d1fae5;
      color: #065f46;
    }
    .status-waiting {
      background-color: #fef3c7;
      color: #92400e;
    }
    .server-alert {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 9999;
      background: #fef3c7;
      border-bottom: 3px solid #f59e0b;
      padding: 16px 24px;
      text-align: center;
      font-weight: 600;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .server-alert a {
      color: #1d4ed8;
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div id="server-alert" class="server-alert" style="display: none;">
    ⚠️ 이 페이지는 <strong>파일로 직접 열면 동작하지 않습니다.</strong><br>
    <strong>start.bat</strong>을 더블클릭해서 서버를 실행한 뒤, 브라우저 주소창에
    <a href="http://localhost:5000" target="_blank">http://localhost:5000</a> 을 입력해 접속해 주세요.
  </div>
  <div class="main-container">
    <h1 class="text-center mb-4" style="color: #111827;">📰 뉴스 요약 챗봇</h1>

    <!-- API 키 설정 섹션 -->
    <div class="section-card">
      <div class="section-title">🔑 재미나이(Gemini) API 키 설정</div>
      <div class="row g-3 align-items-end">
        <div class="col-md-8">
          <label class="form-label">API 키 입력 (내용이 모두 보입니다)</label>
          <input
            type="text"
            class="form-control api-key-input"
            id="api-key-input"
            placeholder="AIzaSyD3a5aGRqW9nOM_WVqCuTmr7d6fDkf9HyY"
            value=""
          />
        </div>
        <div class="col-md-4">
          <button class="btn btn-primary w-100" onclick="validateAndSaveApiKey()">
            검증 및 저장
          </button>
        </div>
      </div>
      <div id="api-validation-result"></div>
    </div>

    <!-- 뉴스 검색 섹션 -->
    <div class="section-card">
      <div class="section-title">
        🔍 뉴스 검색
        <span id="news-status" class="status-badge status-waiting">뉴스 검색 대기 중</span>
      </div>
      <form id="search-form" class="row g-2 mb-3">
        <div class="col-md-9">
          <input
            type="text"
            class="form-control"
            id="search-keyword"
            placeholder="예: 인공지능, 주식, 축구, 경제 전망 ..."
            required
          />
        </div>
        <div class="col-md-3">
          <button type="submit" class="btn btn-primary w-100">
            뉴스 검색
          </button>
        </div>
      </form>
      <div id="search-error" class="alert alert-danger" style="display: none;"></div>
      <div id="summary-box" class="summary-box" style="display: none;">
        <h6 class="fw-bold mb-2">📝 AI 요약</h6>
        <div id="summary-content"></div>
      </div>
      <div id="articles-container"></div>
      <div id="action-buttons" style="display: none; margin-top: 12px;">
        <button class="btn btn-sm btn-info me-2" onclick="generateSummary()">
          📝 AI 요약 생성
        </button>
        <button class="btn btn-sm btn-success" onclick="saveCurrentNews()">
          💾 뉴스 저장하기
        </button>
      </div>
    </div>

    <!-- 2열 레이아웃: 뉴스 목록과 대화 -->
    <div class="grid-layout">
      <!-- 뉴스 목록 -->
      <div class="section-card">
        <div class="section-title">📋 수집된 뉴스 목록</div>
        <div id="articles-list" class="text-muted">
          뉴스를 검색하면 여기에 표시됩니다.
        </div>
      </div>

      <!-- 대화 창 -->
      <div class="section-card">
        <div class="section-title">
          💬 뉴스 대화
          <span id="chat-status" class="status-badge status-waiting">대화 대기 중</span>
        </div>
        <div class="chat-container" id="chat-messages">
          <div class="message bot">
            <strong>안녕하세요! 👋</strong><br><br>
            뉴스를 검색한 후, 여기서 뉴스에 대해 질문해주세요.<br><br>
            <strong>예시 질문:</strong><br>
            • 이 뉴스들의 주요 내용은 무엇인가요?<br>
            • 가장 중요한 기사는 무엇인가요?<br>
            • 이 뉴스들에서 공통된 주제는 무엇인가요?
          </div>
        </div>
        <form id="chat-form" class="row g-2">
          <div class="col-md-9">
            <input
              type="text"
              class="form-control"
              id="chat-input"
              placeholder="뉴스에 대해 질문해보세요..."
              required
            />
          </div>
          <div class="col-md-3">
            <button type="submit" class="btn btn-primary w-100">
              전송
            </button>
          </div>
        </form>
        <div id="chat-loading" style="display: none; text-align: center; padding: 10px; color: #3b82f6;">
          🤔 재미나이 AI가 답변을 생성하고 있습니다...
        </div>
      </div>
    </div>

    <!-- 저장된 뉴스 섹션 -->
    <div class="section-card">
      <div class="section-title">💾 저장된 뉴스</div>
      <button class="btn btn-sm btn-secondary mb-3" onclick="loadSavedNews()">
        새로고침
      </button>
      <div id="saved-news-list">
        <div class="text-muted">저장된 뉴스가 없습니다.</div>
      </div>
    </div>
  </div>

  <script>
    const API_BASE = (window.location.protocol === "file:") ? "http://localhost:5000" : "";
    const NETWORK_MSG = "서버에 연결할 수 없습니다. start.bat을 실행한 뒤 브라우저에서 http://localhost:5000 으로 접속해 주세요.";

    let currentArticles = [];
    let currentKeyword = "";

    function isNetworkError(err) {
      const msg = (err && err.message) ? err.message : String(err);
      return /fetch|network|Failed to load|연결할 수 없습니다|JSON|Unexpected token/i.test(msg);
    }

    // API 키 검증 및 저장
    async function validateAndSaveApiKey() {
      const apiKeyInput = document.getElementById("api-key-input");
      const apiKey = apiKeyInput.value.trim();
      const resultDiv = document.getElementById("api-validation-result");

      if (!apiKey) {
        resultDiv.innerHTML = `
          <div class="validation-result validation-error">
            <strong>❌ API 키가 입력되지 않았습니다.</strong><br>
            재미나이(Gemini) API 키를 입력해주세요.
          </div>
        `;
        return;
      }

      resultDiv.innerHTML = `
        <div class="validation-result" style="background-color: #f3f4f6; border: 1px solid #9ca3af;">
          <strong>⏳ API 키를 검증하는 중...</strong>
        </div>
      `;

      try {
        const resp = await fetch(API_BASE + "/validate-api", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ api_key: apiKey }),
        });
        const data = await resp.json();

        if (data.valid) {
          resultDiv.innerHTML = `
            <div class="validation-result validation-success">
              <strong>${data.message}</strong><br>
              <small>${data.details}</small>
            </div>
          `;
          // 저장
          await fetch(API_BASE + "/save-api-key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: apiKey }),
          });
        } else {
          resultDiv.innerHTML = `
            <div class="validation-result validation-error">
              <strong>${data.message}</strong><br>
              <small>${data.details}</small>
            </div>
          `;
        }
      } catch (err) {
        const detail = isNetworkError(err) ? NETWORK_MSG : err.message;
        resultDiv.innerHTML = `
          <div class="validation-result validation-error">
            <strong>❌ 검증 중 오류 발생</strong><br>
            <small>${detail}</small>
          </div>
        `;
      }
    }

    // 뉴스 검색
    document.getElementById("search-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const keyword = document.getElementById("search-keyword").value.trim();
      if (!keyword) return;

      const errorDiv = document.getElementById("search-error");
      const articlesContainer = document.getElementById("articles-container");
      const articlesList = document.getElementById("articles-list");
      const statusBadge = document.getElementById("news-status");

      errorDiv.style.display = "none";
      articlesContainer.innerHTML = "";
      articlesList.innerHTML = "";
      statusBadge.textContent = "검색 중...";
      statusBadge.className = "status-badge status-waiting";

      try {
        const resp = await fetch(API_BASE + "/search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ keyword: keyword }),
        });
        const data = await resp.json();

        if (data.error) {
          errorDiv.innerHTML = `<strong>${data.message}</strong><br><small>${data.details || ""}</small>`;
          errorDiv.style.display = "block";
          statusBadge.textContent = "검색 실패";
          statusBadge.className = "status-badge status-waiting";
        } else {
          currentArticles = data.articles || [];
          currentKeyword = keyword;

          if (currentArticles.length > 0) {
            statusBadge.textContent = `${currentArticles.length}개 뉴스 수집 완료`;
            statusBadge.className = "status-badge status-ready";

            // 뉴스 목록 표시
            let listHtml = "";
            currentArticles.forEach((article, idx) => {
              listHtml += `
                <div class="article-card">
                  <div class="article-title">
                    ${idx + 1}. ${article.title || "(제목 없음)"}
                  </div>
                  ${article.published ? `<div class="article-meta">${article.published}</div>` : ""}
                </div>
              `;
            });
            articlesList.innerHTML = listHtml;

            // 상세 뉴스 표시
            let detailHtml = `<p class="text-muted mb-2">총 ${currentArticles.length}개의 기사를 찾았습니다.</p>`;
            currentArticles.forEach((article) => {
              detailHtml += `
                <div class="article-card">
                  <div class="article-title">
                    ${article.link ? `<a href="${article.link}" target="_blank">${article.title}</a>` : article.title}
                  </div>
                  ${article.published ? `<div class="article-meta">${article.published}</div>` : ""}
                  <div class="article-summary">${article.summary_short || article.summary || ""}</div>
                </div>
              `;
            });
            articlesContainer.innerHTML = detailHtml;

            // 대화 상태 업데이트
            document.getElementById("chat-status").textContent = `${currentArticles.length}개 뉴스 준비됨`;
            document.getElementById("chat-status").className = "status-badge status-ready";
            
            // 액션 버튼 표시
            document.getElementById("action-buttons").style.display = "block";
          } else {
            statusBadge.textContent = "뉴스를 찾지 못했습니다";
            statusBadge.className = "status-badge status-waiting";
            articlesList.innerHTML = '<div class="text-muted">뉴스를 찾지 못했습니다.</div>';
          }
        }
      } catch (err) {
        const detail = isNetworkError(err) ? NETWORK_MSG : err.message;
        errorDiv.innerHTML = `<strong>오류 발생</strong><br><small>${detail}</small>`;
        errorDiv.style.display = "block";
        statusBadge.textContent = "검색 실패";
        statusBadge.className = "status-badge status-waiting";
      }
    });

    // AI 요약 생성
    async function generateSummary() {
      if (currentArticles.length === 0) {
        alert("요약할 뉴스가 없습니다.");
        return;
      }

      const summaryBox = document.getElementById("summary-box");
      const summaryContent = document.getElementById("summary-content");
      summaryBox.style.display = "block";
      summaryContent.textContent = "요약 생성 중...";

      try {
        const resp = await fetch(API_BASE + "/summarize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ articles: currentArticles }),
        });
        const data = await resp.json();
        if (data.error) {
          summaryContent.innerHTML = `<strong>오류:</strong> ${data.message}<br><small>${data.details || ""}</small>`;
        } else {
          summaryContent.textContent = data.summary;
        }
      } catch (err) {
        summaryContent.textContent = isNetworkError(err) ? NETWORK_MSG : ("요약 생성 중 오류: " + err.message);
      }
    }

    // 채팅 기능
    document.getElementById("chat-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const input = document.getElementById("chat-input");
      const message = input.value.trim();
      if (!message) return;

      if (currentArticles.length === 0) {
        alert("먼저 뉴스를 검색해주세요.");
        return;
      }

      // 사용자 메시지 표시
      const chatMessages = document.getElementById("chat-messages");
      const userMsg = document.createElement("div");
      userMsg.className = "message user";
      userMsg.textContent = message;
      chatMessages.appendChild(userMsg);
      input.value = "";

      // 로딩 표시
      const loading = document.getElementById("chat-loading");
      loading.style.display = "block";

      try {
        const resp = await fetch(API_BASE + "/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            articles: currentArticles,
            message: message,
          }),
        });
        const data = await resp.json();
        if (data.error) {
          const errorMsg = document.createElement("div");
          errorMsg.className = "message bot";
          errorMsg.innerHTML = `<strong>오류:</strong> ${data.message}<br><small>${data.details || ""}</small>`;
          chatMessages.appendChild(errorMsg);
        } else {
          const botMsg = document.createElement("div");
          botMsg.className = "message bot";
          botMsg.textContent = data.response;
          chatMessages.appendChild(botMsg);
        }
      } catch (err) {
        const errorMsg = document.createElement("div");
        errorMsg.className = "message bot";
        errorMsg.textContent = isNetworkError(err) ? NETWORK_MSG : ("오류: " + err.message);
        chatMessages.appendChild(errorMsg);
      } finally {
        loading.style.display = "none";
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    });

    // 뉴스 저장하기
    async function saveCurrentNews() {
      if (!currentKeyword || currentArticles.length === 0) {
        alert("저장할 뉴스가 없습니다.");
        return;
      }

      try {
        const resp = await fetch(API_BASE + "/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            keyword: currentKeyword,
            articles: currentArticles,
          }),
        });
        const data = await resp.json();
        if (data.success) {
          alert("뉴스가 저장되었습니다!");
          loadSavedNews();
        } else {
          alert("저장 실패: " + data.error);
        }
      } catch (err) {
        alert(isNetworkError(err) ? NETWORK_MSG : ("저장 중 오류: " + err.message));
      }
    }

    // 저장된 뉴스 불러오기
    async function loadSavedNews() {
      try {
        const resp = await fetch(API_BASE + "/saved");
        const data = await resp.json();
        const listEl = document.getElementById("saved-news-list");

        if (data.success && data.saved_news.length > 0) {
          let html = "";
          data.saved_news.forEach((item) => {
            html += `
              <div class="article-card mb-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <div>
                    <span class="badge bg-primary">${item.keyword}</span>
                    <span class="text-muted ms-2">${item.timestamp}</span>
                  </div>
                  <span class="badge bg-secondary">${item.articles.length}개 기사</span>
                </div>
              </div>
            `;
          });
          listEl.innerHTML = html;
        } else {
          listEl.innerHTML = '<div class="text-muted">저장된 뉴스가 없습니다.</div>';
        }
      } catch (err) {
        const detail = isNetworkError(err) ? NETWORK_MSG : err.message;
        document.getElementById("saved-news-list").innerHTML =
          '<div class="text-danger">불러오기 오류: ' + detail + "</div>";
      }
    }

    // 페이지 로드 시
    document.addEventListener("DOMContentLoaded", () => {
      if (window.location.protocol === "file:") {
        document.getElementById("server-alert").style.display = "block";
      }
      loadSavedNews();
      document.getElementById("api-key-input").focus();
    });
  </script>

  <script
    src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
    integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz"
    crossorigin="anonymous"
  ></script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    saved_api_key = get_api_key()
    return render_template_string(HTML_TEMPLATE, saved_api_key=saved_api_key)


@app.route("/index2.html", methods=["GET"])
def index2():
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index2.html")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(), 200, {"Content-Type": "text/html; charset=utf-8"}
    except FileNotFoundError:
        return "index2.html not found", 404


@app.route("/index3.html", methods=["GET"])
def index3():
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index3.html")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(), 200, {"Content-Type": "text/html; charset=utf-8"}
    except FileNotFoundError:
        return "index3.html not found", 404


@app.route("/validate-api", methods=["POST"])
def validate_api():
    try:
        data = request.json
        api_key = data.get("api_key", "")
        result = validate_api_key(api_key)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "valid": False,
            "message": "❌ 검증 중 오류 발생",
            "details": str(e)
        })


@app.route("/save-api-key", methods=["POST"])
def save_api():
    try:
        data = request.json
        api_key = data.get("api_key", "")
        if save_api_key(api_key):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "저장 실패"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/search", methods=["POST"])
def search():
    try:
        data = request.json
        keyword = data.get("keyword", "").strip()

        if not keyword:
            return jsonify({
                "error": True,
                "message": "키워드가 입력되지 않았습니다."
            })

        result = fetch_news(keyword, max_results=10)

        if result.get("error"):
            return jsonify({
                "error": True,
                "message": result.get("message", "오류 발생"),
                "details": result.get("details", "")
            })

        articles = result.get("articles", [])
        # 간단한 요약 추가
        from news_chatbot import simple_summarize
        for article in articles:
            article["summary_short"] = simple_summarize(article.get("summary", ""))

        return jsonify({
            "error": False,
            "articles": articles
        })

    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"검색 중 오류 발생: {str(e)}"
        })


@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        data = request.json
        articles = data.get("articles", [])

        if not articles:
            return jsonify({
                "error": True,
                "message": "뉴스가 없습니다."
            })

        # 원본 summary 필드가 있는지 확인
        raw_articles = []
        for a in articles:
            raw_articles.append({
                "title": a.get("title"),
                "summary": a.get("summary") or a.get("summary_short", ""),
                "published": a.get("published"),
            })

        result = summarize_with_gemini(raw_articles)
        if result.get("error"):
            return jsonify({
                "error": True,
                "message": result.get("message", "오류 발생"),
                "details": result.get("details", "")
            })
        return jsonify({
            "error": False,
            "summary": result.get("summary", "")
        })

    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"요약 중 오류 발생: {str(e)}"
        })


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        articles = data.get("articles", [])
        message = data.get("message", "")

        if not articles:
            return jsonify({
                "error": True,
                "message": "뉴스가 없습니다."
            })

        if not message:
            return jsonify({
                "error": True,
                "message": "메시지가 없습니다."
            })

        # 원본 summary 필드가 있는지 확인
        raw_articles = []
        for a in articles:
            raw_articles.append({
                "title": a.get("title"),
                "summary": a.get("summary") or a.get("summary_short", ""),
                "published": a.get("published"),
            })

        result = chat_with_gemini(raw_articles, message)
        if result.get("error"):
            return jsonify({
                "error": True,
                "message": result.get("message", "오류 발생"),
                "details": result.get("details", "")
            })
        return jsonify({
            "error": False,
            "response": result.get("response", "")
        })

    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"대화 중 오류 발생: {str(e)}"
        })


@app.route("/save", methods=["POST"])
def save():
    try:
        data = request.json
        keyword = data.get("keyword", "")
        articles = data.get("articles", [])

        if not keyword or not articles:
            return jsonify({"success": False, "error": "키워드 또는 뉴스가 없습니다."})

        # 원본 summary 필드가 있는지 확인
        raw_articles = []
        for a in articles:
            raw_articles.append({
                "title": a.get("title"),
                "link": a.get("link"),
                "summary": a.get("summary") or a.get("summary_short", ""),
                "published": a.get("published"),
            })

        save_news(keyword, raw_articles)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/saved", methods=["GET"])
def saved():
    try:
        saved_news = load_saved_news()
        return jsonify({"success": True, "saved_news": saved_news})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
