#!/usr/bin/env python3
"""インストール済みの yomiyasu プラグインから yomiyasu_lint.py の場所を解決する。

探索順:
  1. 環境変数 YOMIYASU_LINT（ファイルパスを直接指定）
  2. ~/.claude/plugins/installed_plugins.json の yomiyasu の installPath
  3. ~/.claude/plugins/cache/yomiyasu/yomiyasu/<version>/ のうち最新バージョン
  4. npx skills / openskills での配置先（~/.claude/skills, ~/.agents/skills）
見つからなければ終了コード3で、インストール方法を案内する。
"""
import json
import os
import re
import sys
from pathlib import Path

INSTALL_HINT = (
    "yomiyasu_lint.py が見つかりません。yomiyasu プラグインをインストールしてください。\n"
    "  /plugin marketplace add nanaism/yomiyasu\n"
    "  /plugin install yomiyasu@yomiyasu\n"
    "別の場所にある場合は環境変数 YOMIYASU_LINT でパスを指定できます。"
)


def _version_key(p: Path):
    return [int(x) if x.isdigit() else x for x in re.split(r"[.\-]", p.name)]


def resolve() -> Path | None:
    env = os.environ.get("YOMIYASU_LINT")
    if env and Path(env).is_file():
        return Path(env)

    home = Path.home()
    rel = Path("scripts/yomiyasu_lint.py")

    reg = home / ".claude/plugins/installed_plugins.json"
    if reg.is_file():
        try:
            plugins = json.loads(reg.read_text(encoding="utf-8")).get("plugins", {})
            for key, entries in plugins.items():
                if key.split("@")[0] != "yomiyasu":
                    continue
                for e in entries:
                    cand = Path(e.get("installPath", "")) / rel
                    if cand.is_file():
                        return cand
        except (json.JSONDecodeError, OSError):
            pass

    cache = home / ".claude/plugins/cache/yomiyasu/yomiyasu"
    if cache.is_dir():
        for v in sorted(cache.iterdir(), key=_version_key, reverse=True):
            if (v / rel).is_file():
                return v / rel

    for base in (home / ".claude/skills/yomiyasu", home / ".agents/skills/yomiyasu"):
        if (base / rel).is_file():
            return base / rel
    return None


if __name__ == "__main__":
    p = resolve()
    if p is None:
        print(INSTALL_HINT, file=sys.stderr)
        sys.exit(3)
    print(p)
