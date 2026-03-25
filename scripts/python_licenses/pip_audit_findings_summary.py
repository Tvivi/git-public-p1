"""pip-audit の JSON レポートから GitHub Actions 用サマリーを生成するスクリプト。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


NO_VULN_MESSAGE = "No known vulnerabilities found ✅"
MISSING_REPORT_MESSAGE = "pip-audit report not found ⚠️"


def load_report(report_path: str) -> dict[str, Any] | None:
    """pip-audit の JSON レポートを読み込む。

    Args:
        report_path: JSON レポートのファイルパス。

    Returns:
        JSON を辞書として返す。ファイルが存在しない場合は None。
    """
    path = Path(report_path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def iter_vulnerabilities(report: dict[str, Any]) -> list[dict[str, Any]]:
    """レポートから脆弱性一覧を平坦化して返す。"""
    findings: list[dict[str, Any]] = []
    for dependency in report.get("dependencies", []):
        vulns = dependency.get("vulns") or []
        if not vulns:
            continue
        for vuln in vulns:
            findings.append(
                {
                    "name": dependency.get("name", "unknown"),
                    "version": dependency.get("version", "unknown"),
                    "id": vuln.get("id", "unknown"),
                    "fix_versions": vuln.get("fix_versions") or [],
                }
            )
    return findings


def build_summary(*, title: str, report_path: str, dev_scope: bool) -> str:
    """pip-audit 用の Markdown サマリー文字列を生成する。

    Args:
        title: サマリーに表示する見出し。
        report_path: pip-audit JSON レポートのパス。
        dev_scope: 開発依存を含むチェックかどうか。

    Returns:
        GITHUB_STEP_SUMMARY に追記できる Markdown 文字列。
    """
    lines = [f"## {title}", ""]
    report = load_report(report_path)

    if report is None:
        lines.extend(
            [
                MISSING_REPORT_MESSAGE,
                "",
                "### 💡 Fix hints",
                "- Confirm that `pip-audit` actually ran",
                "- Re-run locally with: `uv run pip-audit --format=json`",
                "",
            ]
        )
        return "\n".join(lines)

    findings = iter_vulnerabilities(report)
    if not findings:
        lines.extend([NO_VULN_MESSAGE, ""])
        return "\n".join(lines)

    vulnerable_package_count = len({(item["name"], item["version"]) for item in findings})
    lines.extend([f"Found {vulnerable_package_count} vulnerable package(s) ❌", ""])

    for item in findings:
        fix_versions = ", ".join(item["fix_versions"]) if item["fix_versions"] else "none suggested"
        lines.append(f"- **{item['name']}@{item['version']}**: {item['id']}")
        lines.append(f"  - Fix version(s): {fix_versions}")

    lines.extend(
        [
            "",
            "### 💡 Fix hints",
            "- Update vulnerable packages directly: `uv add <package>@latest`",
            "- Or refresh lock file broadly: `uv lock --upgrade`",
            "- Inspect dependency tree: `uv tree`",
        ]
    )

    if dev_scope:
        lines.append("- Dev-only vulnerabilities can sometimes be fixed by upgrading test / lint tools only")

    lines.extend(["- Re-run locally: `uv run pip-audit`", ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(
        description="pip-audit の結果を GitHub Actions サマリーへ出力する"
    )
    parser.add_argument("--title", required=True, help="サマリーの見出し")
    parser.add_argument("--report-path", required=True, help="pip-audit JSON レポートのパス")
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
        dev_scope=args.dev_scope,
    )
    with Path(args.output).open("a", encoding="utf-8") as f:
        f.write(summary + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
