"""
Gitleaks の実行結果を解析し、CI用サマリーと評価結果を生成するスクリプト。

このスクリプトは以下を担う：

- Gitleaks JSON レポートの読み込み
- findings の集計
- 人間向け Markdown サマリーの生成
- GitHub Actions 用の出力（GITHUB_OUTPUT）
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.security.common import load_json_file, write_github_output


def load_findings(path: Path) -> list[dict[str, Any]]:
    """
    GitleaksのJSONレポートから findings を読み込む。

    Parameters
    ----------
    path : Path
        JSONファイルのパス

    Returns
    -------
    list[dict[str, Any]]
        有効な finding のリスト
    """
    data = load_json_file(path)
    if not isinstance(data, list):
        return []

    return [item for item in data if isinstance(item, dict)]


def build_hint(findings: list[dict[str, Any]], scan_exit_code: int) -> str:
    """
    findings から簡易サマリーを生成する。

    Parameters
    ----------
    findings : list[dict[str, Any]]
        Gitleaks の finding 一覧
    scan_exit_code : int
        Gitleaks 実行時の終了コード

    Returns
    -------
    str
        サマリー表向けの短いヒント
    """
    if scan_exit_code != 0 and not findings:
        return "scan error"

    if not findings:
        return "No leaks found"

    rules: Counter[str] = Counter()
    paths: Counter[str] = Counter()

    for finding in findings:
        rule = finding.get("RuleID") or finding.get("Description") or "unknown rule"
        file_path = finding.get("File") or "unknown file"
        rules[str(rule)] += 1
        paths[str(file_path)] += 1

    top_rule, top_rule_count = rules.most_common(1)[0]
    top_path, top_path_count = paths.most_common(1)[0]

    return (
        f"{len(findings)} findings, "
        f"top rule: {top_rule} ({top_rule_count}), "
        f"top file: {top_path} ({top_path_count})"
    )


def write_summary(
    path: Path,
    findings: list[dict[str, Any]],
    scan_exit_code: int,
) -> None:
    """
    Markdown形式のサマリーファイルを生成する。

    生の finding 詳細や commit / author は書き出さず、
    集計情報だけを公開向け summary に残す。

    Parameters
    ----------
    path : Path
        出力先Markdownファイル
    findings : list[dict[str, Any]]
        Gitleaks の finding 一覧
    scan_exit_code : int
        Gitleaks 実行時の終了コード
    """
    lines = ["### 🔐 Gitleaks findings", ""]

    if scan_exit_code != 0 and not findings:
        lines.append("- Gitleaks scan failed to run")
        lines.append(
            "- Hint: check install step, CLI args, repository state, or JSON output path"
        )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    if not findings:
        lines.append("- No leaks found")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    lines.append(f"- Total findings: **{len(findings)}**")
    lines.append("")

    rules: Counter[str] = Counter()
    for finding in findings:
        rule = finding.get("RuleID") or finding.get("Description") or "unknown rule"
        rules[str(rule)] += 1

    lines.append("#### Top matched rules")
    for rule, count in rules.most_common(5):
        lines.append(f"- {rule}: {count}")
    lines.append("")

    lines.append("#### Result")
    lines.append("- Detailed finding locations are intentionally omitted from this summary")
    lines.append("- Review the raw CI artifact or protected scan output for exact locations")
    lines.append("")
    lines.append("#### Hint")
    lines.append("- If this is a real secret: revoke or rotate it first")
    lines.append("- Remove it from the repository and history if needed")
    lines.append(
        "- If false positive: tune `.gitleaks.toml` or `.gitleaksignore` carefully"
    )
    lines.append(
        "- If test data triggers detection: isolate fixtures and add narrow allow rules"
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """
    CLIエントリーポイント。

    Returns
    -------
    int
        常に0を返す。
        CIの最終失敗判定は Workflow 側で行う。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--summary-file", required=True)
    parser.add_argument("--scan-exit-code", required=True, type=int)
    args = parser.parse_args()

    findings = load_findings(Path(args.input))
    summary_path = Path(args.summary_file)
    summary_hint = build_hint(findings, args.scan_exit_code)

    write_summary(summary_path, findings, args.scan_exit_code)

    scan_status = "error" if args.scan_exit_code != 0 and not findings else "ok"
    policy_exit_code = 1 if findings else 0

    outputs = {
        "scan_status": scan_status,
        "scan_exit_code": str(args.scan_exit_code),
        "policy_exit_code": str(policy_exit_code),
        "finding_count": str(len(findings)),
        "summary_hint": summary_hint,
        "summary_file": str(summary_path),
    }

    for key, value in outputs.items():
        print(f"{key}={value}")

    write_github_output(outputs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
