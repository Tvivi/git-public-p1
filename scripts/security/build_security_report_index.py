"""
セキュリティレポートの索引Markdownを生成するスクリプト。

このスクリプトは以下を担う：

- detect-secrets / Gitleaks / Trivy の各サマリーの入口を1つにまとめる
- 公開向け index に生の検出内容を埋め込まない
- summary 本文を再保存せず、存在確認と固定文だけを出力する
"""

from __future__ import annotations

import argparse
from pathlib import Path


def build_section(title: str, summary_path: Path) -> str:
    """
    1つのレポート用セクションを構築する。

    summary 本文は読み込まず、存在有無だけで表示を分ける。

    Parameters
    ----------
    title : str
        セクション見出し
    summary_path : Path
        個別サマリーのパス

    Returns
    -------
    str
        Markdown セクション文字列
    """
    lines = [f"## {title}", ""]

    if summary_path.exists():
        lines.append(f"- Summary file: `{summary_path.name}`")
        lines.append("- Detailed findings are intentionally not embedded in this index.")
        lines.append("- Open the individual artifact or report file for review.")
    else:
        lines.append(f"- Summary file is missing: `{summary_path.name}`")

    lines.append("")
    return "\n".join(lines)


def build_index(
    detect_summary_path: Path,
    gitleaks_summary_path: Path,
    trivy_config_summary_path: Path,
    trivy_fs_summary_path: Path,
) -> str:
    """
    公開用の索引Markdown文字列を構築する。

    Parameters
    ----------
    detect_summary_path : Path
        detect-secrets サマリーパス
    gitleaks_summary_path : Path
        Gitleaks サマリーパス
    trivy_config_summary_path : Path
        Trivy config サマリーパス
    trivy_fs_summary_path : Path
        Trivy fs サマリーパス

    Returns
    -------
    str
        Markdown文字列
    """
    parts = [
        "# Repository Security Reports",
        "",
        "このページは CI で生成されたセキュリティレポートの索引です。",
        "公開向け index では詳細な検出内容を再掲せず、各レポートの入口だけを表示します。",
        "",
        build_section("detect-secrets", detect_summary_path),
        build_section("Gitleaks", gitleaks_summary_path),
        build_section("Trivy config", trivy_config_summary_path),
        build_section("Trivy fs", trivy_fs_summary_path),
    ]
    return "\n".join(parts) + "\n"


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
        detect_summary_path=Path(args.detect_secrets_summary),
        gitleaks_summary_path=Path(args.gitleaks_summary),
        trivy_config_summary_path=Path(args.trivy_config_summary),
        trivy_fs_summary_path=Path(args.trivy_fs_summary),
    )

    Path(args.output).write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
