"""
gitleaks_summary.py のユニットテスト。

テスト対象：
- JSON読み込み（load_findings）
- ヒント生成（build_hint）
- Markdown生成（write_summary）
- CLI統合（main）

CI環境に依存せずローカル実行可能にするため：
- GITHUB_OUTPUT は monkeypatch で差し替え
- sys.argv も monkeypatch で差し替え
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.security.gitleaks_summary import (
    build_hint,
    load_findings,
    main,
    write_summary,
)


def test_load_findings_missing_file(tmp_path: Path) -> None:
    """存在しないファイルは空リストを返す。"""
    assert load_findings(tmp_path / "missing.json") == []


def test_load_findings_blank_file(tmp_path: Path) -> None:
    """空ファイルは空リストになる。"""
    path = tmp_path / "findings.json"
    path.write_text("", encoding="utf-8")
    assert load_findings(path) == []


def test_load_findings_filters_non_dict(tmp_path: Path) -> None:
    """list内のdict以外は除外される。"""
    path = tmp_path / "findings.json"
    path.write_text(json.dumps([{"a": 1}, "x", 1]), encoding="utf-8")
    assert load_findings(path) == [{"a": 1}]


def test_build_hint_scan_error() -> None:
    """scan失敗かつfindingsなしなら scan error になる。"""
    assert build_hint([], 1) == "scan error"


def test_build_hint_no_leaks() -> None:
    """findingsなしなら No leaks found になる。"""
    assert build_hint([], 0) == "No leaks found"


def test_build_hint_with_findings() -> None:
    """findingsありなら件数と代表的なルール・ファイルが出る。"""
    findings = [
        {"RuleID": "key", "File": "a.py"},
        {"RuleID": "key", "File": "a.py"},
        {"RuleID": "pw", "File": "b.py"},
    ]
    hint = build_hint(findings, 1)

    assert "3 findings" in hint
    assert "top rule: key (2)" in hint
    assert "top file: a.py (2)" in hint


def test_write_summary_no_findings(tmp_path: Path) -> None:
    """findingsなしの場合は No leaks が出力される。"""
    out = tmp_path / "summary.md"
    write_summary(out, [], 0)

    text = out.read_text(encoding="utf-8")
    assert "No leaks found" in text


def test_write_summary_with_findings_omits_raw_details(tmp_path: Path) -> None:
    """findingsありでも詳細な場所情報は出力しない。"""
    out = tmp_path / "summary.md"
    findings = [
        {"RuleID": "key", "File": "a.py", "StartLine": 1},
        {"RuleID": "key", "File": "a.py", "StartLine": 2},
    ]
    write_summary(out, findings, 1)

    text = out.read_text(encoding="utf-8")
    assert "Total findings: **2**" in text
    assert "Top matched rules" in text
    assert "Detailed finding locations are intentionally omitted" in text
    assert "`a.py`" not in text
    assert "[line: 1]" not in text


def test_main_with_findings_sets_policy_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """findingsありの場合は policy failure になる。"""
    input_path = tmp_path / "in.json"
    summary_path = tmp_path / "out.md"
    github_output = tmp_path / "gh.txt"

    input_path.write_text(
        json.dumps([{"RuleID": "k", "File": "a.py"}]),
        encoding="utf-8",
    )

    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    monkeypatch.setattr(
        "sys.argv",
        [
            "x",
            "--input",
            str(input_path),
            "--summary-file",
            str(summary_path),
            "--scan-exit-code",
            "1",
        ],
    )

    main()
    captured = capsys.readouterr()

    assert "policy_exit_code=1" in captured.out
    assert "scan_status=ok" in captured.out


def test_main_scan_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """scan失敗でJSONも無い場合は scan_status=error になる。"""
    input_path = tmp_path / "missing.json"
    summary_path = tmp_path / "out.md"
    github_output = tmp_path / "gh.txt"

    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    monkeypatch.setattr(
        "sys.argv",
        [
            "x",
            "--input",
            str(input_path),
            "--summary-file",
            str(summary_path),
            "--scan-exit-code",
            "2",
        ],
    )

    main()
    captured = capsys.readouterr()

    assert "scan_status=error" in captured.out
    assert "summary_hint=scan error" in captured.out
