#!/usr/bin/env python3
"""Claude Code の Stop hook。最終応答を yomiyasu_lint で検査し、結果を通知する。

環境変数:
  YOMIYASU_HOOK_MODE       warn (既定) | block | off
                           warn:  スコアと指摘を警告として表示するだけ
                           block: スコアが閾値未満なら1回だけ書き直しを求める（2回目以降は warn と同じ）
  YOMIYASU_HOOK_THRESHOLD  block の閾値（既定 90）
  YOMIYASU_HOOK_MIN_LEN    この文字数未満の応答は検査しない（既定 200）
  YOMIYASU_HOOK_LOG        検査結果を追記する JSONL（既定 ~/.claude/yomiyasu-chat/lint-log.jsonl、空文字で無効）
  YOMIYASU_LINT            yomiyasu_lint.py のパスを直接指定（省略時はインストール済み yomiyasu から解決。
                           同じディレクトリに markdown_visibility.py が必要）

yomiyasu が未インストール、または検査中に失敗した場合は何もせず終了する（フェイルオープン）。
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from yomiyasu_lint_path import resolve  # noqa: E402

MARKER = re.compile(r"^\s*\[yomiyasu\]\s*$", re.M)
JAPANESE = re.compile(r"[぀-ヿ一-鿿]")
STATE_DIR = Path(tempfile.gettempdir()) / "yomiyasu-chat-hook"


def emit(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False))


def already_blocked(session_id: str, prompt_id: str) -> bool:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    f = STATE_DIR / f"{session_id}-{prompt_id}"
    if f.exists():
        return True
    f.write_text(str(time.time()))
    return False


def summarize(findings: list, limit: int = 3) -> str:
    lines = []
    for f in findings[:limit]:
        snippet = (f.get("snippet") or "").strip()
        if len(snippet) > 40:
            snippet = snippet[:40] + "…"
        lines.append(f"- [{f.get('severity', '').upper()}] {f.get('rule')}: {snippet}")
    rest = len(findings) - limit
    if rest > 0:
        lines.append(f"- ほか{rest}件")
    return "\n".join(lines)


def append_log(log_path: str, data: dict, text: str, score: int, findings: list) -> None:
    if not log_path:
        return
    try:
        p = Path(log_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps({
                "ts": int(time.time()),
                "session_id": data.get("session_id"),
                "cwd": data.get("cwd"),
                "chars": len(text),
                "score": score,
                "rules": [f.get("rule") for f in findings],
            }, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main() -> None:
    mode = os.environ.get("YOMIYASU_HOOK_MODE", "warn").lower()
    if mode == "off":
        return
    threshold = int(os.environ.get("YOMIYASU_HOOK_THRESHOLD", "90"))
    min_len = int(os.environ.get("YOMIYASU_HOOK_MIN_LEN", "200"))
    log_path = os.environ.get(
        "YOMIYASU_HOOK_LOG", str(Path.home() / ".claude/yomiyasu-chat/lint-log.jsonl"))

    data = json.load(sys.stdin)
    text = MARKER.sub("", data.get("last_assistant_message") or "").strip()
    if len(text) < min_len or not JAPANESE.search(text):
        return

    lint = resolve()
    if lint is None:
        return
    r = subprocess.run([sys.executable, str(lint), "--json"], input=text, text=True,
                       capture_output=True, timeout=20)
    if r.returncode not in (0, 1) or not r.stdout.strip():
        return
    result = json.loads(r.stdout)
    score = result.get("score", 100)
    findings = result.get("findings", [])

    append_log(log_path, data, text, score, findings)

    if not findings:
        return

    head = f"yomiyasu_lint: {score}/100（{len(findings)}件）"

    if mode == "block" and score < threshold and not already_blocked(
            str(data.get("session_id")), str(data.get("prompt_id"))):
        detail = "\n".join(
            f"- L{f.get('line')} {f.get('rule')}: {f.get('message')}\n  > {f.get('snippet')}"
            for f in findings)
        emit({
            "decision": "block",
            "reason": (f"{head}。閾値{threshold}未満のため、直前の応答を次の指摘に沿って書き直してください。"
                       f"意味は変えず、文体だけを直します。\n{detail}"),
        })
        return

    emit({"systemMessage": f"{head}\n{summarize(findings)}"})


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # フェイルオープン
        print(f"yomiyasu_stop_hook: {e}", file=sys.stderr)
    sys.exit(0)
