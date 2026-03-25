"""
セキュリティ補助スクリプト向けの共通ユーティリティ。

このモジュールは以下を担う：

- JSONファイルの安全な読み込み
- テキストファイルの安全な読み込み
- GitHub Actions の GITHUB_OUTPUT への安全な書き込み
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> Any | None:
    """
    JSONファイルを安全に読み込む。

    Parameters
    ----------
    path : Path
        読み込むファイルパス

    Returns
    -------
    Any | None
        読み込んだJSON値。
        ファイル不存在・空ファイル・不正JSON時は ``None`` を返す。
    """
    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def load_text_file(path: Path) -> str:
    """
    テキストファイルを安全に読み込む。

    Parameters
    ----------
    path : Path
        読み込むファイルパス

    Returns
    -------
    str
        ファイル内容。存在しない場合は空文字を返す。
    """
    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8").strip()


def write_github_output(outputs: dict[str, str]) -> None:
    """
    GitHub Actions の GITHUB_OUTPUT に値を書き込む。

    Parameters
    ----------
    outputs : dict[str, str]
        出力するキーと値
    """
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        return

    output_path = Path(github_output)
    with output_path.open("a", encoding="utf-8") as file:
        for key, value in outputs.items():
            if "\n" in value:
                file.write(f"{key}<<EOF\n{value}\nEOF\n")
            else:
                file.write(f"{key}={value}\n")
