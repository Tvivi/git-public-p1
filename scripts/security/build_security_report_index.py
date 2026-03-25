"""
セキュリティレポートの索引Markdownを生成するスクリプト。

このスクリプトは以下を担う：

- detect-secrets / Gitleaks / Trivy の各サマリーを1つに束ねる
- GitHub Actions artifact から Pages 公開へ移行しやすい入口ページを作る
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
            "",
            "## detect-secrets",
            "",
            detect_summary_md.strip(),
            "",
            "## Gitleaks",
            "",
            gitleaks_summary.strip(),
            "",
            "## Trivy config",
            "",
            trivy_config_summary.strip(),
            "",
            "## Trivy fs",
            "",
            trivy_fs_summary.strip(),
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
