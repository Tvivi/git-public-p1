"""ライセンス違反チェック結果を GitHub Actions のサマリーへ追記するスクリプト。"""

from __future__ import annotations

import argparse
from pathlib import Path


SUCCESS_MESSAGE = "No disallowed licenses detected ✅"
FAILURE_MESSAGE = "Disallowed license policy check failed ❌"


def build_summary(*, title: str, report_path: str, policy_outcome: str, dev_scope: bool) -> str:
    """ライセンス違反チェック用の Markdown サマリー文字列を生成する。

    Args:
        title: サマリーに表示する見出し。
        report_path: 参照先として表示する JSON レポートのパス。
        policy_outcome: GitHub Actions の step outcome。通常は success / failure。
        dev_scope: 開発依存を含むチェックかどうか。

    Returns:
        GITHUB_STEP_SUMMARY に追記できる Markdown 文字列。
    """
    lines = [f"## {title}", ""]

    if policy_outcome == "success":
        lines.extend([SUCCESS_MESSAGE, ""])
        return "\n".join(lines)

    lines.extend(
        [
            FAILURE_MESSAGE,
            "",
            "### 💡 Fix hints",
            f"- Check the full license report: `{report_path}`",
            "- Identify which package uses GPL / AGPL / LGPL",
            "- Replace the package with a permissive alternative if possible",
        ]
    )

    if dev_scope:
        lines.append("- Dev-only packages may be removable from CI or local tooling dependencies")
    else:
        lines.append(
            "- If the package is truly required, review redistribution obligations before publishing"
        )

    lines.extend(["- Check dependency tree with: `uv tree`", ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(
        description="ライセンス違反チェック結果を GitHub Actions サマリーへ出力する"
    )
    parser.add_argument("--title", required=True, help="サマリーの見出し")
    parser.add_argument("--report-path", required=True, help="JSON レポートのパス")
    parser.add_argument(
        "--policy-outcome",
        required=True,
        choices=["success", "failure", "cancelled", "skipped"],
        help="GitHub Actions の step outcome",
    )
    parser.add_argument(
        "--dev-scope",
        action="store_true",
        help="開発依存を含むチェックの場合に指定する",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="追記先ファイル。通常は $GITHUB_STEP_SUMMARY",
    )
    return parser.parse_args()


def main() -> int:
    """引数を受け取り、サマリーをファイルへ追記する。"""
    args = parse_args()
    summary = build_summary(
        title=args.title,
        report_path=args.report_path,
        policy_outcome=args.policy_outcome,
        dev_scope=args.dev_scope,
    )
    with Path(args.output).open("a", encoding="utf-8") as f:
        f.write(summary + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
