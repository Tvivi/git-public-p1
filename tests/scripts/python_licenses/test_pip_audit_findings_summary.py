"""pip_audit_findings_summary.py のテスト。"""

import json
from pathlib import Path

from scripts.python_licenses.pip_audit_findings_summary import build_summary, iter_vulnerabilities, load_report


def test_load_report_returns_none_when_file_not_found(tmp_path: Path) -> None:
    """存在しないレポートは None を返す。"""
    assert load_report(str(tmp_path / "missing.json")) is None


def test_iter_vulnerabilities_flattens_dependencies() -> None:
    """依存パッケージごとの脆弱性を平坦化できる。"""
    report = {
        "dependencies": [
            {
                "name": "requests",
                "version": "2.0.0",
                "vulns": [
                    {"id": "PYSEC-1", "fix_versions": ["2.1.0"]},
                    {"id": "GHSA-2", "fix_versions": []},
                ],
            },
            {"name": "pytest", "version": "8.0.0", "vulns": []},
        ]
    }

    findings = iter_vulnerabilities(report)

    assert findings == [
        {
            "name": "requests",
            "version": "2.0.0",
            "id": "PYSEC-1",
            "fix_versions": ["2.1.0"],
        },
        {
            "name": "requests",
            "version": "2.0.0",
            "id": "GHSA-2",
            "fix_versions": [],
        },
    ]


def test_build_summary_when_report_is_missing(tmp_path: Path) -> None:
    """レポート未生成時は再実行ヒントを返す。"""
    summary = build_summary(
        title="All Python vulnerability findings (including dev)",
        report_path=str(tmp_path / "missing.json"),
        dev_scope=True,
    )

    assert "pip-audit report not found ⚠️" in summary
    assert "Re-run locally with: `uv run pip-audit --format=json`" in summary


def test_build_summary_when_no_vulnerabilities(tmp_path: Path) -> None:
    """脆弱性が無い場合は成功メッセージを返す。"""
    report_path = tmp_path / "pip-audit.json"
    report_path.write_text(json.dumps({"dependencies": [{"name": "pytest", "version": "8.0.0", "vulns": []}]}), encoding="utf-8")

    summary = build_summary(
        title="Production Python vulnerability findings",
        report_path=str(report_path),
        dev_scope=False,
    )

    assert "No known vulnerabilities found ✅" in summary
    assert "Fix hints" not in summary


def test_build_summary_when_vulnerabilities_exist(tmp_path: Path) -> None:
    """脆弱性がある場合は一覧と修正ヒントを返す。"""
    report = {
        "dependencies": [
            {
                "name": "requests",
                "version": "2.28.0",
                "vulns": [
                    {"id": "PYSEC-123", "fix_versions": ["2.31.0"]},
                ],
            },
            {
                "name": "urllib3",
                "version": "1.25.0",
                "vulns": [
                    {"id": "GHSA-999", "fix_versions": []},
                ],
            },
        ]
    }
    report_path = tmp_path / "pip-audit.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    summary = build_summary(
        title="All Python vulnerability findings (including dev)",
        report_path=str(report_path),
        dev_scope=True,
    )

    assert "Found 2 vulnerable package(s) ❌" in summary
    assert "**requests@2.28.0**: PYSEC-123" in summary
    assert "Fix version(s): 2.31.0" in summary
    assert "**urllib3@1.25.0**: GHSA-999" in summary
    assert "Fix version(s): none suggested" in summary
    assert "Dev-only vulnerabilities can sometimes be fixed" in summary
