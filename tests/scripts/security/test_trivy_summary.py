"""
trivy_summary.py のユニットテスト。

テスト対象：
- JSON読み込み
- findings 抽出
- Markdown生成
- ヒント生成
"""

from __future__ import annotations

from pathlib import Path

from scripts.security.trivy_summary import (
    Finding,
    build_markdown,
    build_summary_hint,
    find_config_findings,
    find_fs_findings,
    load_json,
)


def test_load_json_missing_file(tmp_path: Path) -> None:
    """存在しないJSONファイルは空辞書になる。"""
    assert load_json(tmp_path / "missing.json") == {}


def test_build_markdown_no_findings() -> None:
    """findingsが空のとき、正常メッセージが出ることを確認する。"""
    markdown = build_markdown("config", [])
    assert "No HIGH/CRITICAL findings" in markdown


def test_build_markdown_scan_error() -> None:
    """scan_error=True のとき、エラーメッセージが出ることを確認する。"""
    markdown = build_markdown("config", [], scan_error=True)
    assert "scan failed to run" in markdown


def test_find_config_findings_extracts_only_high_and_critical() -> None:
    """config結果から HIGH / CRITICAL だけ抽出される。"""
    data = {
        "Results": [
            {
                "Target": ".devcontainer/Dockerfile",
                "Misconfigurations": [
                    {
                        "Severity": "HIGH",
                        "Title": "Bad config",
                        "ID": "DS-0017",
                        "CauseMetadata": {
                            "StartLine": 43,
                            "EndLine": 44,
                        },
                    },
                    {
                        "Severity": "LOW",
                        "Title": "Ignore me",
                        "ID": "LOW-0001",
                        "CauseMetadata": {
                            "StartLine": 1,
                            "EndLine": 1,
                        },
                    },
                ],
            }
        ]
    }

    findings = find_config_findings(data)

    assert findings == [
        Finding(
            severity="HIGH",
            title="Bad config",
            rule_id="DS-0017",
            target=".devcontainer/Dockerfile",
            detail="[lines: 43-44]",
        )
    ]


def test_find_fs_findings_extracts_vulns_misconfigs_and_secrets() -> None:
    """fs結果から Vulnerabilities / Misconfigurations / Secrets を抽出する。"""
    data = {
        "Results": [
            {
                "Target": "requirements.txt",
                "Vulnerabilities": [
                    {
                        "Severity": "CRITICAL",
                        "PkgName": "requests",
                        "InstalledVersion": "2.0.0",
                        "FixedVersion": "2.32.0",
                        "VulnerabilityID": "CVE-9999",
                    }
                ],
                "Misconfigurations": [
                    {
                        "Severity": "HIGH",
                        "Title": "Bad setting",
                        "ID": "CFG-0001",
                    }
                ],
                "Secrets": [
                    {
                        "Severity": "HIGH",
                        "RuleID": "generic-api-key",
                    }
                ],
            }
        ]
    }

    findings = find_fs_findings(data)

    assert findings == [
        Finding(
            severity="CRITICAL",
            title="requests 2.0.0 → 2.32.0",
            rule_id="CVE-9999",
            target="requirements.txt",
            detail="",
        ),
        Finding(
            severity="HIGH",
            title="Bad setting",
            rule_id="CFG-0001",
            target="requirements.txt",
            detail="",
        ),
        Finding(
            severity="HIGH",
            title="secret detected",
            rule_id="generic-api-key",
            target="requirements.txt",
            detail="",
        ),
    ]


def test_build_summary_hint_no_findings() -> None:
    """findingsなしなら正常メッセージになる。"""
    assert build_summary_hint([]) == "No HIGH/CRITICAL findings"


def test_build_summary_hint_scan_error() -> None:
    """scan失敗時は scan failed になる。"""
    assert build_summary_hint([], scan_error=True) == "scan failed"


def test_build_summary_hint_with_findings() -> None:
    """findingsありなら件数と先頭検出結果がヒントに入る。"""
    data = {
        "Results": [
            {
                "Target": ".github/workflows/security.yml",
                "Misconfigurations": [
                    {
                        "Severity": "HIGH",
                        "Title": "Bad config",
                        "ID": "CFG-9999",
                        "CauseMetadata": {
                            "StartLine": 1,
                            "EndLine": 2,
                        },
                    }
                ],
            }
        ]
    }

    findings = find_config_findings(data)
    hint = build_summary_hint(findings)

    assert "1 finding(s)" in hint
    assert "CFG-9999" in hint
    assert ".github/workflows/security.yml" in hint
