"""
Trivy のスキャン結果（config / fs）JSONを解析し、
GitHub Actions 用のサマリーと出力値を生成するスクリプト。

主な役割：
- HIGH / CRITICAL のみ抽出
- Markdown形式のレポート生成
- GitHub Actions の output (GITHUB_OUTPUT) に結果を書き込み
- scan error / policy failure / success を分離
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.security.common import load_json_file, write_github_output


SEVERITIES = {"HIGH", "CRITICAL"}


@dataclass(frozen=True)
class Finding:
    """
    Trivy の検出結果1件を表すデータクラス。

    Attributes
    ----------
    severity : str
        重大度 (HIGH / CRITICAL)
    title : str
        問題のタイトルや概要
    rule_id : str
        ルールID / 脆弱性ID
    target : str
        対象ファイルやパッケージ
    detail : str
        追加情報（行番号など）
    """

    severity: str
    title: str
    rule_id: str
    target: str
    detail: str


def load_json(path: Path) -> dict[str, Any]:
    """
    JSONファイルを読み込み、辞書として返す。

    Parameters
    ----------
    path : Path
        読み込むJSONファイルのパス

    Returns
    -------
    dict[str, Any]
        JSON内容。不正形式なら空辞書。
    """
    data = load_json_file(path)
    return data if isinstance(data, dict) else {}


def build_line_detail(cause_metadata: dict[str, Any]) -> str:
    """
    Trivy の行番号情報から表示用の詳細文字列を生成する。

    Parameters
    ----------
    cause_metadata : dict[str, Any]
        CauseMetadata の辞書

    Returns
    -------
    str
        表示用の行情報。行番号が無ければ空文字。
    """
    start_line = cause_metadata.get("StartLine") or 0
    end_line = cause_metadata.get("EndLine") or 0

    if start_line and end_line:
        return f"[lines: {start_line}-{end_line}]"

    return ""


def find_config_findings(data: dict[str, Any]) -> list[Finding]:
    """
    Trivy config スキャン結果から HIGH / CRITICAL のみ抽出する。

    Parameters
    ----------
    data : dict[str, Any]
        Trivy config のJSONデータ

    Returns
    -------
    list[Finding]
        抽出された Finding のリスト
    """
    findings: list[Finding] = []

    for result in data.get("Results", []) or []:
        target = result.get("Target") or "unknown"
        for misconfig in result.get("Misconfigurations", []) or []:
            severity = misconfig.get("Severity", "")
            if severity not in SEVERITIES:
                continue

            cause = misconfig.get("CauseMetadata") or {}
            findings.append(
                Finding(
                    severity=severity,
                    title=misconfig.get("Title") or "unknown",
                    rule_id=misconfig.get("ID") or "unknown",
                    target=target,
                    detail=build_line_detail(cause),
                )
            )

    return findings


def find_fs_findings(data: dict[str, Any]) -> list[Finding]:
    """
    Trivy fs スキャン結果から HIGH / CRITICAL を抽出する。

    対象：
    - Vulnerabilities
    - Misconfigurations
    - Secrets

    Parameters
    ----------
    data : dict[str, Any]
        Trivy fs のJSONデータ

    Returns
    -------
    list[Finding]
        抽出された Finding のリスト
    """
    findings: list[Finding] = []

    for result in data.get("Results", []) or []:
        target = result.get("Target") or "unknown"

        for vuln in result.get("Vulnerabilities", []) or []:
            severity = vuln.get("Severity", "")
            if severity not in SEVERITIES:
                continue

            pkg_name = vuln.get("PkgName") or "unknown"
            installed = vuln.get("InstalledVersion") or "unknown"
            fixed = vuln.get("FixedVersion") or "no fix"
            vuln_id = vuln.get("VulnerabilityID") or "unknown"

            findings.append(
                Finding(
                    severity=severity,
                    title=f"{pkg_name} {installed} → {fixed}",
                    rule_id=vuln_id,
                    target=target,
                    detail="",
                )
            )

        for misconfig in result.get("Misconfigurations", []) or []:
            severity = misconfig.get("Severity", "")
            if severity not in SEVERITIES:
                continue

            findings.append(
                Finding(
                    severity=severity,
                    title=misconfig.get("Title") or "unknown",
                    rule_id=misconfig.get("ID") or "unknown",
                    target=target,
                    detail="",
                )
            )

        for secret in result.get("Secrets", []) or []:
            severity = secret.get("Severity", "")
            if severity not in SEVERITIES:
                continue

            findings.append(
                Finding(
                    severity=severity,
                    title="secret detected",
                    rule_id=secret.get("RuleID") or "unknown",
                    target=target,
                    detail="",
                )
            )

    return findings


def build_markdown(
    scan_type: str,
    findings: list[Finding],
    scan_error: bool = False,
) -> str:
    """
    検出結果を GitHub 表示用の Markdown に変換する。

    Parameters
    ----------
    scan_type : str
        "config" または "fs"
    findings : list[Finding]
        検出結果一覧
    scan_error : bool
        スキャン失敗かどうか

    Returns
    -------
    str
        Markdown文字列
    """
    lines = [f"### 🔍 Trivy {scan_type} findings (HIGH/CRITICAL)", ""]

    if scan_error:
        lines.append(f"- Trivy {scan_type} scan failed to run")
        if scan_type == "config":
            lines.append(
                "- Hint: check Trivy installation, network access, and target files"
            )
        else:
            lines.append(
                "- Hint: check vulnerability DB download, dependency files, and network access"
            )
        return "\n".join(lines) + "\n"

    if not findings:
        lines.append("- No HIGH/CRITICAL findings (trivyignore applied)")
        return "\n".join(lines) + "\n"

    for finding in findings:
        suffix = f" {finding.detail}" if finding.detail else ""
        lines.append(
            f"- [{finding.severity}] {finding.title} "
            f"({finding.rule_id}) in {finding.target}{suffix}"
        )

    return "\n".join(lines) + "\n"


def build_summary_hint(
    findings: list[Finding],
    scan_error: bool = False,
) -> str:
    """
    GitHub Actions のサマリー表用の短いヒントを生成する。

    Parameters
    ----------
    findings : list[Finding]
        検出結果一覧
    scan_error : bool
        スキャン失敗かどうか

    Returns
    -------
    str
        短いヒント文字列
    """
    if scan_error:
        return "scan failed"

    if not findings:
        return "No HIGH/CRITICAL findings"

    first = findings[0]
    head = f"{len(findings)} finding(s): [{first.severity}] {first.rule_id} in {first.target}"
    return head[:160]


def main() -> int:
    """
    CLIエントリーポイント。

    Returns
    -------
    int
        常に0
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan-type", choices=["config", "fs"], required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--summary-file", required=True)
    parser.add_argument("--scan-exit-code", required=True, type=int)
    args = parser.parse_args()

    input_path = Path(args.input)
    summary_path = Path(args.summary_file)

    scan_error = args.scan_exit_code != 0
    data = load_json(input_path)

    if args.scan_type == "config":
        findings = find_config_findings(data)
    else:
        findings = find_fs_findings(data)

    summary_md = build_markdown(args.scan_type, findings, scan_error=scan_error)
    summary_path.write_text(summary_md, encoding="utf-8")

    outputs = {
        "scan_status": "error" if scan_error else "ok",
        "scan_exit_code": str(args.scan_exit_code),
        "policy_exit_code": str(99 if scan_error else (1 if findings else 0)),
        "finding_count": str(len(findings)),
        "summary_hint": build_summary_hint(findings, scan_error=scan_error),
        "summary_file": str(summary_path),
    }

    for key, value in outputs.items():
        print(f"{key}={value}")

    write_github_output(outputs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
