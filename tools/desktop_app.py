"""Native Windows desktop shell for the local finance workspace."""
from __future__ import annotations

import ctypes
import os
import sys
import threading
import traceback
from http.server import ThreadingHTTPServer
from pathlib import Path


APP_TITLE = "NUVEXA 工作台"
APP_DATA_NAME = "NUVEXA/RomaniaFinanceSkillHub"


# Keep resource discovery compatible with source runs and PyInstaller bundles.
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
TOOLS_DIR = BUNDLE_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from finance_skill_api import make_handler  # noqa: E402


def app_data_dir() -> Path:
    """Return a per-user location that survives app upgrades and uninstall."""
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / APP_DATA_NAME
    return Path.home() / ".local" / "share" / "RomaniaFinanceSkillHub"


def _show_error(message: str, log_path: Path | None = None) -> None:
    if log_path is not None:
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(message + "\n\n" + traceback.format_exc(), encoding="utf-8")
        except OSError:
            pass
    if os.name == "nt":
        try:
            ctypes.windll.user32.MessageBoxW(None, message, APP_TITLE, 0x10)
            return
        except Exception:
            pass
    print(message, file=sys.stderr)


def main() -> int:
    data_dir = app_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    log_path = data_dir / "logs" / "desktop-startup.log"

    try:
        import webview
    except Exception as exc:
        _show_error(
            "桌面界面组件无法启动。请确认安装包完整；若问题持续，请查看本机应用数据目录中的 desktop-startup.log。\n\n"
            + str(exc),
            log_path,
        )
        return 1

    handler = make_handler(data_dir, desktop_mode=True)

    class QuietHandler(handler):
        def log_message(self, _format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    server.daemon_threads = True
    port = server.server_address[1]
    server_thread = threading.Thread(target=server.serve_forever, name="finance-local-api", daemon=True)
    server_thread.start()

    try:
        webview.create_window(
            APP_TITLE,
            f"http://127.0.0.1:{port}/",
            width=1440,
            height=940,
            min_size=(960, 640),
            background_color="#ffffff",
        )
        webview.start(gui="edgechromium", debug=False)
        return 0
    except Exception as exc:
        _show_error(
            "无法打开桌面工作台。请确认 Microsoft Edge WebView2 Runtime 已安装，然后重新启动。\n\n"
            + str(exc),
            log_path,
        )
        return 1
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=3)


if __name__ == "__main__":
    raise SystemExit(main())
