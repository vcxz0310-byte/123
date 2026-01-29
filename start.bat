@echo off
chcp 65001 >nul
echo ========================================
echo   뉴스 요약 챗봇 서버 시작
echo ========================================
echo.

REM 필요한 라이브러리 설치 확인 (pip 대신 python -m pip 사용)
echo [1/3] 라이브러리 확인 중...
python -c "import flask, requests, feedparser, google.generativeai, flask_cors" 2>nul
if errorlevel 1 (
    echo 라이브러리가 설치되지 않았습니다. 설치를 시작합니다...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo py 로 시도합니다...
        py -m pip install -r requirements.txt
        if errorlevel 1 (
            echo 오류: 라이브러리 설치에 실패했습니다.
            echo Python 이 설치되어 있는지, PATH에 등록되어 있는지 확인해 주세요.
            pause
            exit /b 1
        )
    )
)

echo [2/3] Flask 서버 시작 중...
echo.
echo 서버가 켜지면 브라우저가 자동으로 열립니다.
echo 서버를 중지하려면 '뉴스 챗봇 서버' 창을 닫으세요.
echo.
echo ========================================
echo   접속 주소: http://localhost:5000
echo ========================================
echo.

REM 새 창에서 서버 실행 후 브라우저 열기
start "뉴스 챗봇 서버" python news_chatbot_web.py
timeout /t 3 /nobreak >nul
start http://localhost:5000/index2.html
echo 브라우저가 열렸습니다. 이 창은 닫아도 됩니다.
pause
