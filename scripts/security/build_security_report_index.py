"""
セキュリティレポートの索引Markdownを生成するスクリプト。

このスクリプトは以下を担う：

- detect-secrets / Gitleaks / Trivy の各サマリーの入口を1つにまとめる
- 公開向け index に生の検出詳細を埋め込まず、要約だけを載せる
"""

from __future__ import annotations

import argparse
from pathlib import Path


def load_text(path: Path) -> str:
    """
    テキストファイルを読み込む。

    Parameters
    ----------
    path : Path
        対象ファイル

    Returns
    -------
    str
        ファイル内容。存在しなければ簡易メッセージを返す。
    """
    if not path.exists():
        return f"_Missing file: `{path}`_\n"

    return path.read_text(encoding="utf-8").strip() + "\n"


def build_section_preview(summary_text: str) -> str:
    """
    サマリー本文から安全な短いプレビューだけを抽出する。

    生の findings や code block を再掲しないため、以下を除外する：
    - コードブロック
    - 見出し
    - 空行

    Parameters
    ----------
    summary_text : str
        元のサマリー本文

    Returns
    -------
    str
        index 用の短いプレビューMarkdown
    """
    lines: list[str] = []
    in_code_block = False

    for raw_line in summary_text.splitlines():
        line = raw_line.strip()

        if raw_line.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block or not line:
            continue

        if line.startswith("#"):
            continue

        lines.append(line)

    if not lines:
        return "- Summary available in artifact"

    preview_lines = lines[:3]
    return "\n".join(f"- {line}" for line in preview_lines)


def build_index(
    detect_summary_md: str,
    gitleaks_summary: str,
    trivy_config_summary: str,
    trivy_fs_summary: str,
) -> str:
    """
    公開用の索引Markdown文字列を構築する。

    Parameters
    ----------
    detect_summary_md : str
        detect-secrets サマリー本文
    gitleaks_summary : str
        Gitleaks サマリー本文
    trivy_config_summary : str
        Trivy config サマリー本文
    trivy_fs_summary : str
        Trivy fs サマリー本文

    Returns
    -------
    str
        Markdown文字列
    """
    return "\n".join(
        [
            "# Repository Security Reports",
            "",
            "このページは CI で生成されたセキュリティレポートの索引です。",
            "公開向け index では詳細な検出内容を再掲せず、要約のみを表示します。",
            "",
            "## detect-secrets",
            "",
            build_section_preview(detect_summary_md),
            "",
            "## Gitleaks",
            "",
            build_section_preview(gitleaks_summary),
            "",
            "## Trivy config",
            "",
            build_section_preview(trivy_config_summary),
            "",
            "## Trivy fs",
            "",
            build_section_preview(trivy_fs_summary),
            "",
        ]
    ) + "\n"


def main() -> int:
    """
    CLIエントリーポイント。

    Returns
    -------
    int
        常に0
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--detect-secrets-summary", required=True)
    parser.add_argument("--gitleaks-summary", required=True)
    parser.add_argument("--trivy-config-summary", required=True)
    parser.add_argument("--trivy-fs-summary", required=True)
    args = parser.parse_args()

    content = build_index(
        detect_summary_md=load_text(Path(args.detect_secrets_summary)),
        gitleaks_summary=load_text(Path(args.gitleaks_summary)),
        trivy_config_summary=load_text(Path(args.trivy_config_summary)),
        trivy_fs_summary=load_text(Path(args.trivy_fs_summary)),
    )

    Path(args.output).write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
