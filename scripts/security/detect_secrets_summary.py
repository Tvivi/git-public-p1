"""
detect-secrets の実行結果を解析し、CI用サマリーと評価結果を生成するスクリプト。

このスクリプトは以下を担う：

- detect-secrets scan のJSONレポート確認
- detect-secrets-hook の終了コード評価
- 人間向け Markdown サマリーの生成
- GitHub Actions 用の出力（GITHUB_OUTPUT）

想定ユースケース：
- baseline との差分に基づく新規シークレット検出
- scan error / policy failure / success の分離
- GitHub Actions の summary / PR comment / artifact 用中間成果物生成
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from scripts.security.common import load_json_file, load_text_file, write_github_output


def load_report(path: Path) -> dict[str, Any]:
    """
    detect-secrets scan のJSONレポートを読み込む。

    Parameters
    ----------
    path : Path
        JSONファイルのパス

    Returns
    -------
    dict[str, Any]
        読み込んだJSON辞書。
        存在しない / 空 / 不正形式なら空辞書を返す。
    """
    data = load_json_file(path)
    return data if isinstance(data, dict) else {}


def count_report_findings(report: dict[str, Any]) -> int:
    """
    detect-secrets scan レポートに含まれる検出件数を数える。

    Parameters
    ----------
    report : dict[str, Any]
        detect-secrets scan のJSON辞書

    Returns
    -------
    int
        検出件数
    """
    results = report.get("results")
    if not isinstance(results, dict):
        return 0

    count = 0
    for findings in results.values():
        if isinstance(findings, list):
            count += sum(1 for item in findings if isinstance(item, dict))

    return count


def load_hook_output(path: Path) -> str:
    """
    detect-secrets-hook の標準出力 / 標準エラーを読み込む。

    Parameters
    ----------
    path : Path
        hook出力ファイル

    Returns
    -------
    str
        読み込んだ文字列。存在しなければ空文字。
    """
    return load_text_file(path)


def build_hint(
    report_findings: int,
    scan_exit_code: int,
    hook_exit_code: int,
    hook_output: str,
) -> str:
    """
    サマリー表向けの短いヒントを生成する。

    Parameters
    ----------
    report_findings : int
        working-tree scan の検出件数
    scan_exit_code : int
        detect-secrets scan の終了コード
    hook_exit_code : int
        detect-secrets-hook の終了コード
    hook_output : str
        hookの出力内容

    Returns
    -------
    str
        短いヒント文字列
    """
    if scan_exit_code != 0:
        return "scan error"

    if hook_exit_code == 0:
        return "No new secrets"

    first_line = hook_output.splitlines()[0].strip() if hook_output else ""
    if first_line:
        short = first_line[:120]
        return f"Potential new secrets detected: {short}"

    return (
        "Potential new secrets detected "
        f"({report_findings} findings in working tree scan)"
    )


def write_summary(
    path: Path,
    report_findings: int,
    scan_exit_code: int,
    hook_exit_code: int,
    hook_output: str,
) -> None:
    """
    Markdown形式のサマリーファイルを生成する。

    Parameters
    ----------
    path : Path
        出力先Markdownファイル
    report_findings : int
        working-tree scan の検出件数
    scan_exit_code : int
        detect-secrets scan の終了コード
    hook_exit_code : int
        detect-secrets-hook の終了コード
    hook_output : str
        hookの出力内容
    """
    lines: list[str] = ["### 🔐 detect-secrets findings", ""]

    if scan_exit_code != 0:
        lines.append("- detect-secrets scan failed to run")
        lines.append(
            "- Hint: check detect-secrets installation, CLI args, and tracked files"
        )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    lines.append(f"- Working-tree scan findings: **{report_findings}**")
    lines.append(f"- Baseline policy: **{'pass' if hook_exit_code == 0 else 'fail'}**")
    lines.append("")

    if hook_exit_code == 0:
        lines.append("#### Result")
        lines.append("- No new secrets compared with `.secrets.baseline`")
        lines.append("")
        lines.append("#### Hint")
        lines.append("- Keep `.secrets.baseline` reviewed and minimal")
        lines.append("- Re-run audit when intentional test fixtures change")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    lines.append("#### Hook output")
    lines.append("")
    lines.append("```text")
    lines.append(hook_output or "(no output)")
    lines.append("```")
    lines.append("")
    lines.append("#### Hint")
    lines.append("- Remove the secret from tracked files if it is real")
    lines.append("- Rotate or revoke the credential before rewriting history")
    lines.append("- If this is a false positive, audit `.secrets.baseline` carefully")
    lines.append("- Narrow allowlisting is safer than broad ignores")

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
    parser.add_argument("--report", required=True)
    parser.add_argument("--hook-output", required=True)
    parser.add_argument("--summary-file", required=True)
    parser.add_argument("--scan-exit-code", required=True, type=int)
    parser.add_argument("--hook-exit-code", required=True, type=int)
    args = parser.parse_args()

    report = load_report(Path(args.report))
    report_findings = count_report_findings(report)
    hook_output = load_hook_output(Path(args.hook_output))

    summary_hint = build_hint(
        report_findings=report_findings,
        scan_exit_code=args.scan_exit_code,
        hook_exit_code=args.hook_exit_code,
        hook_output=hook_output,
    )

    write_summary(
        path=Path(args.summary_file),
        report_findings=report_findings,
        scan_exit_code=args.scan_exit_code,
        hook_exit_code=args.hook_exit_code,
        hook_output=hook_output,
    )

    scan_status = "ok" if args.scan_exit_code == 0 else "error"
    policy_exit_code = 1 if args.hook_exit_code != 0 else 0

    outputs = {
        "scan_status": scan_status,
        "scan_exit_code": str(args.scan_exit_code),
        "policy_exit_code": str(policy_exit_code),
        "finding_count": str(report_findings),
        "summary_hint": summary_hint,
        "summary_file": args.summary_file,
    }

    for key, value in outputs.items():
        print(f"{key}={value}")

    write_github_output(outputs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
