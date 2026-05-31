import os
import json
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

PMAP = {
    "idea": "아이디어 발굴", "product": "상품 기획", "blog": "블로그 글쓰기",
    "content": "콘텐츠 기획", "study": "공부 정리", "problem": "문제 해결",
    "plan": "계획 세우기", "meeting": "회의 준비"
}
MMAP = {
    "wide": "다양한 방향으로 넓게",
    "deep": "한 주제를 세부적으로 깊게",
    "action": "실제 행동 가능한 항목 위주로",
    "creative": "평범하지 않은 창의적 아이디어 포함",
    "realistic": "바로 실행 가능한 현실적 항목 위주로"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/mindmap", methods=["POST"])
def mindmap():
    data = request.get_json()
    topic = data.get("topic", "")
    purpose = data.get("purpose", "idea")
    mode = data.get("mode", "wide")
    parent_title = data.get("parent_title", None)
    depth = data.get("depth", 0)

    is_root = depth == 0
    if is_root:
        context = f'중심 주제: "{topic}"\n목적: {PMAP.get(purpose, topic)}\n확장 방식: {MMAP.get(mode, "넓게")}'
    else:
        context = f'중심 주제: "{topic}"\n현재 가지: "{parent_title}"\n목적: {PMAP.get(purpose, topic)}'

    prompt = f"""{context}

위 내용을 바탕으로 마인드맵 가지를 정확히 6개 제안하라.

규칙:
- 서로 겹치지 않는 방향
- 짧고 명확한 제목 (10자 이내 권장)
- 실제로 활용 가능한 내용
- 반드시 JSON 배열만 출력하고 다른 텍스트 없음

출력 형식:
[{{"title":"가지 제목","desc":"한 줄 설명 (20자 이내)"}},...]\
"""

    if not ANTHROPIC_API_KEY:
        return jsonify({"ok": False, "error": "ANTHROPIC_API_KEY 환경변수가 없습니다"}), 500

    try:
        res = requests.post(
            ANTHROPIC_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        if res.status_code != 200:
            return jsonify({"ok": False, "error": f"Anthropic API 오류 {res.status_code}: {res.text}"}), 500

        result = res.json()
        text = "".join(b.get("text", "") for b in result.get("content", []))
        clean = text.replace("```json", "").replace("```", "").strip()
        branches = json.loads(clean)
        return jsonify({"ok": True, "branches": branches})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
