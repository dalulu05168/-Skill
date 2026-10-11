"""Local-only P004 fictional director studio: casting, real optional Ollama,
editorial review and explicitly authorized SQLite adoption.

This is a real HTTP interface, not a static preview. No internet dependency,
paid API, messaging, trading, account creation or automatic publishing.
"""
from __future__ import annotations

import html
import json
import os
import re
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from director_workflow import prepare, review
from approve_scene import finalize

ROOT = Path(__file__).resolve().parents[1]
DRAFT_ROSTER = ROOT / "characters" / "drafts" / "roster-v2.json"
APPROVED_ROSTER = ROOT / "characters" / "approved-roster.json"
STUDIO_HTML = ROOT / "studio.html"
ID = re.compile(r"^[A-Za-z0-9_-]{25,80}$")
MAX_BODY = 750_000


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + secrets.token_hex(6) + ".tmp")
    try:
        with open(temporary, "x", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _model_name():
    return os.environ.get("P004_OLLAMA_MODEL", "").strip()


def _ollama_generate(prompt):
    """Actually call a local model; no simulated responses or remote URL input."""
    model = _model_name()
    if not model or len(model) > 128:
        raise ValueError("未配置本地模型：设置 P004_OLLAMA_MODEL 为已安装的 Ollama 模型名称")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json", "stream": False,
        "options": {"temperature": 0.55}
    }, ensure_ascii=False).encode("utf-8")
    req = Request("http://127.0.0.1:11434/api/chat", data=body,
                  headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=90) as resp:
            raw = resp.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("AI 返回内容过大")
        result = json.loads(raw)
        output = result.get("message", {}).get("content")
        if not isinstance(output, str) or not output.strip():
            raise ValueError("本地模型未返回对白 JSON")
        return output
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("无法调用本地 Ollama，请确认服务已启动、模型已安装：" + str(exc)) from exc


class StudioServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, data_dir):
        super().__init__(address, StudioHandler)
        self.data_dir = Path(data_dir).expanduser().resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.drafts_dir = self.data_dir / "drafts"
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.history_db = self.data_dir / "adopted-scenes.sqlite3"
        self.csrf_token = secrets.token_urlsafe(24)
        self.write_lock = threading.RLock()

    def save(self, token, state):
        if not ID.fullmatch(token):
            raise ValueError("无效工作会话")
        with self.write_lock:
            _write_atomic(self.drafts_dir / (token + ".json"), state)

    def load(self, token):
        if not isinstance(token, str) or not ID.fullmatch(token):
            raise ValueError("无效工作会话")
        path = self.drafts_dir / (token + ".json")
        if not path.is_file():
            raise ValueError("工作会话不存在")
        with self.write_lock:
            return _read_json(path)


class StudioHandler(BaseHTTPRequestHandler):
    server: StudioServer

    def log_message(self, fmt, *args):
        # Avoid logging story text, authorization data, prompts or session IDs.
        if self.path.split("?")[0] not in ("/", "/api/status"):
            return
        super().log_message(fmt, *args)

    def _host_allowed(self):
        port = self.server.server_port
        return self.headers.get("Host", "") in (
            "127.0.0.1:" + str(port), "localhost:" + str(port)
        )

    def _send(self, status, data, kind="application/json; charset=utf-8"):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False).encode("utf-8")
        elif isinstance(data, str):
            data = data.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; script-src 'unsafe-inline'; "
                         "style-src 'unsafe-inline'; connect-src 'self'; "
                         "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._host_allowed():
            return self._send(403, {"error": "只允许本机访问"})
        if self.path == "/":
            doc = STUDIO_HTML.read_text(encoding="utf-8")
            doc = doc.replace("__STUDIO_CSRF__", html.escape(self.server.csrf_token, quote=True))
            return self._send(200, doc, "text/html; charset=utf-8")
        if self.path == "/api/status":
            approved = _read_json(APPROVED_ROSTER)
            count = len(approved.get("characters", []))
            return self._send(200, {
                "name": "P004 独立导演工作台",
                "candidate_personas": len(_read_json(DRAFT_ROSTER)["people"]),
                "approved_personas": count,
                "local_model_configured": bool(_model_name()),
                "local_model_name": _model_name() or None,
                "mode": "FICTIONAL_EDUCATIONAL_REHEARSAL",
                "public_message_sending": False, "trading_enabled": False,
                "adoption_requires_approval": True,
                "ready_for_final_adoption": count == 65
            })
        return self._send(404, {"error": "未找到页面"})

    def do_POST(self):
        if not self._host_allowed():
            return self._send(403, {"error": "只允许本机访问"})
        origin = self.headers.get("Origin")
        if origin and origin not in ("http://" + self.headers["Host"],):
            return self._send(403, {"error": "禁止跨域操作"})
        if self.headers.get("X-Director-Token") != self.server.csrf_token:
            return self._send(403, {"error": "缺少本机页面验证令牌"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._send(400, {"error": "无效请求长度"})
        if length < 2 or length > MAX_BODY:
            return self._send(413, {"error": "请求内容过大或为空"})
        try:
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("请求必须为 JSON 对象")
            if self.path == "/api/prepare":
                result = self._prepare(payload)
            elif self.path == "/api/generate":
                result = self._generate(payload)
            elif self.path == "/api/review":
                result = self._review(payload)
            elif self.path == "/api/adopt":
                result = self._adopt(payload)
            elif self.path == "/api/load":
                result = self._load(payload)
            else:
                return self._send(404, {"error": "接口不存在"})
            return self._send(200, result)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return self._send(400, {"error": str(exc)[:600]})
        except RuntimeError as exc:
            return self._send(503, {"error": str(exc)[:600]})
        except Exception:
            self.log_error("Internal studio operation failed")
            return self._send(500, {"error": "内部执行失败，未标记成功；请检查本机日志"})

    def _prepare(self, data):
        topic = data.get("topic", "")
        if not isinstance(topic, str) or not 2 <= len(topic.strip()) <= 240:
            raise ValueError("请输入2–240字的虚构故事话题")
        keywords = [k.strip() for k in re.split(r"[,，、;\n]+", topic) if k.strip()]
        if len(keywords) > 12:
            keywords = keywords[:12]
        keywords = [k[:50] for k in keywords]
        request = {
            "scene_id": data.get("scene_id"),
            "story_date": data.get("story_date"),
            "daypart": data.get("daypart"),
            "topic_keywords": keywords,
            "max_members": data.get("max_members", 8),
            "simulation_only": True, "source_status": "HYPOTHETICAL",
            "director_override": data.get("director_note", "")
        }
        prepared = prepare(_read_json(DRAFT_ROSTER), request)
        token = secrets.token_urlsafe(24)
        state = {"prepared": prepared, "draft": None, "qa": None, "adopted": False}
        self.server.save(token, state)
        return {"token": token, "prepared": prepared, "qa": None,
                "message": "已真实完成选角；尚未生成对白"}

    def _load(self, data):
        state = self.server.load(data.get("token"))
        return {"token": data["token"], **state}

    def _generate(self, data):
        token = data.get("token")
        state = self.server.load(token)
        if state.get("adopted"):
            raise ValueError("已采用的场次不可重新生成，请创建新场次")
        if not _model_name():
            raise RuntimeError("未设置 P004_OLLAMA_MODEL；请配置本地免费 Ollama 模型，或使用下方粘贴 JSON 审稿")
        prepared = state["prepared"]
        issues = []
        attempts = []
        for index in range(1, 4):
            prompt = prepared["llm_prompt"]
            if issues:
                prompt += "\n请纠正以下阻断项，只返回整份合法JSON：\n" + "; ".join(issues)
            raw = _ollama_generate(prompt)
            try:
                manuscript = json.loads(raw)
            except json.JSONDecodeError:
                manuscript = None
            qa = review(prepared, manuscript)
            attempts.append({"round": index, "status": qa["status"],
                             "blocking_issues": qa["blocking_issues"]})
            if not qa["blocking_issues"]:
                state["draft"], state["qa"] = manuscript, qa
                self.server.save(token, state)
                return {"token": token, "manuscript": manuscript,
                        "qa": qa, "attempts": attempts,
                        "ai_generation_performed": True,
                        "status": "EDITORIAL_REVIEW_REQUIRED"}
            issues = qa["blocking_issues"]
        state["draft"] = None
        state["qa"] = None
        self.server.save(token, state)
        return {"token": token, "status": "BLOCKED_REWRITE_REQUIRED",
                "attempts": attempts, "ai_generation_performed": True,
                "message": "AI输出连续3次未过结构校验，未保存为合格对白"}

    def _review(self, data):
        token = data.get("token")
        state = self.server.load(token)
        if state.get("adopted"):
            raise ValueError("已采用场次不可再次修改")
        manuscript = data.get("manuscript")
        qa = review(state["prepared"], manuscript)
        state["draft"] = manuscript if not qa["blocking_issues"] else None
        state["qa"] = qa
        self.server.save(token, state)
        return {"token": token, "qa": qa, "manuscript": manuscript,
                "actual_ai_generation_performed": False}

    def _adopt(self, data):
        token = data.get("token")
        state = self.server.load(token)
        if state.get("adopted"):
            raise ValueError("场次已采用，请勿重复提交")
        if state.get("qa", {}).get("status") != "EDITORIAL_REVIEW_REQUIRED" or not state.get("draft"):
            raise ValueError("先通过剧本审稿，不能采用未校验的草稿")
        if (data.get("operator_confirmed") is not True or
                data.get("editorial_confirmed") is not True):
            raise ValueError("必须分别勾选操作者和编辑审稿确认")
        if len(_read_json(APPROVED_ROSTER)["characters"]) != 65:
            raise ValueError("正式65人人物名单尚未获批准，禁止把候选剧情写入正式记忆")
        with self.server.write_lock:
            result = finalize(state["prepared"], state["draft"],
                              db_path=self.server.history_db,
                              approved_roster_path=APPROVED_ROSTER,
                              operator_confirmed=True, editorial_confirmed=True)
            state["adopted"] = True
            self.server.save(token, state)
        return {"result": result, "published": False}


def create_server(port=8765, data_dir=None):
    if data_dir is None:
        data_dir = os.environ.get("P004_DIRECTOR_DATA_DIR") or (
            Path.home() / ".p004-director")
    return StudioServer(("127.0.0.1", int(port)), data_dir)


def main():
    port = int(os.environ.get("P004_DIRECTOR_PORT", "8765"))
    server = create_server(port)
    url = "http://127.0.0.1:" + str(server.server_port) + "/"
    print("P004 导演编剧工作台（仅本机）", flush=True)
    print(url, flush=True)
    print("本地 AI 模型：" + (_model_name() or "未配置（可手动粘贴剧本审稿）"),
          flush=True)
    try:
        webbrowser.open(url)
        server.serve_forever()
    except KeyboardInterrupt:
        print("已停止本机导演工作台")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
