"""
detect_secrets_summary.py のユニットテスト。

テスト対象：
- JSON読み込み
- 検出件数カウント
- ヒント生成
- Markdown生成
- CLI統合
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.security.detect_secrets_summary import (
    build_hint,
    count_report_findings,
    load_hook_output,
    load_report,
    main,
    write_summary,
)


def test_load_report_missing_file(tmp_path: Path) -> None:
    """存在しないファイルは空辞書を返す。"""
    assert load_report(tmp_path / "missing.json") == {}


def test_count_report_findings_counts_all_dict_items() -> None:
    """results配下のdict要素だけ件数として数える。"""
    report = {
        "results": {
            "a.py": [{"type": "Secret Keyword"}, {"type": "Hex High Entropy String"}],
            "b.py": [{"type": "AWS Access Key"}],
            "c.py": ["invalid"],
        }
    }
    assert count_report_findings(report) == 3


def test_load_hook_output_missing_file(tmp_path: Path) -> None:
    """存在しないhook出力ファイルは空文字になる。"""
    assert load_hook_output(tmp_path / "missing.txt") == ""


def test_build_hint_scan_error() -> None:
    """scan失敗時はscan errorになる。"""
    hint = build_hint(
        report_findings=0,
        scan_exit_code=1,
        hook_exit_code=1,
        hook_output="",
    )
    assert hint == "scan error"


def test_build_hint_no_new_secrets() -> None:
    """hook成功時は新規シークレットなしのヒントになる。"""
    hint = build_hint(
        report_findings=2,
        scan_exit_code=0,
        hook_exit_code=0,
        hook_output="",
    )
    assert hint == "No new secrets"


def test_build_hint_with_hook_output_does_not_expose_raw_text() -> None:
    """hook失敗時も生の出力はヒントに含めない。"""
    hint = build_hint(
        report_findings=2,
        scan_exit_code=0,
        hook_exit_code=1,
        hook_output="Potential secret in README.md\nmore lines",
    )
    assert "Potential new secrets detected" in hint
    assert "2 findings in working tree scan" in hint
    assert "Potential secret in README.md" not in hint


def test_write_summary_success(tmp_path: Path) -> None:
    """hook成功時は成功用サマリーが出力される。"""
    out = tmp_path / "summary.md"
    write_summary(
        path=out,
        report_findings=2,
        scan_exit_code=0,
        hook_exit_code=0,
        hook_output="",
    )

    text = out.read_text(encoding="utf-8")
    assert "No new secrets compared with `.secrets.baseline`" in text


def test_write_summary_failure_omits_hook_output(tmp_path: Path) -> None:
    """hook失敗時も生のhook出力はサマリーに書かれない。"""
    out = tmp_path / "summary.md"
    write_summary(
        path=out,
        report_findings=2,
        scan_exit_code=0,
        hook_exit_code=1,
        hook_output="Potential secret in README.md",
    )

    text = out.read_text(encoding="utf-8")
    assert "Potential new secrets detected" in text
    assert "Raw hook output is intentionally omitted" in text
    assert "Potential secret in README.md" not in text
    assert "Hook output" not in text


def test_main_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """正常系ではpolicy_exit_code=0になる。"""
    report = tmp_path / "detect-secrets.json"
    hook = tmp_path / "hook.txt"
    summary = tmp_path / "summary.md"
    github_output = tmp_path / "github_output.txt"

    report.write_text(
        json.dumps({"results": {"a.py": [{"type": "Secret Keyword"}]}}),
        encoding="utf-8",
    )
    hook.write_text("", encoding="utf-8")

    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    monkeypatch.setattr(
        "sys.argv",
        [
            "x",
            "--report",
            str(report),
            "--hook-output",
            str(hook),
            "--summary-file",
            str(summary),
            "--scan-exit-code",
            "0",
            "--hook-exit-code",
            "0",
        ],
    )

    main()
    captured = capsys.readouterr()

    assert "policy_exit_code=0" in captured.out
    assert "scan_status=ok" in captured.out


def test_main_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """baseline違反時はpolicy_exit_code=1になる。"""
    report = tmp_path / "detect-secrets.json"
    hook = tmp_path / "hook.txt"
    summary = tmp_path / "summary.md"
    github_output = tmp_path / "github_output.txt"

    report.write_text(
        json.dumps({"results": {"a.py": [{"type": "Secret Keyword"}]}}),
        encoding="utf-8",
    )
    hook.write_text("Potential secret in a.py", encoding="utf-8")

    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    monkeypatch.setattr(
        "sys.argv",
        [
            "x",
            "--report",
            str(report),
            "--hook-output",
            str(hook),
            "--summary-file",
            str(summary),
            "--scan-exit-code",
            "0",
            "--hook-exit-code",
            "1",
        ],
    )

    main()
    captured = capsys.readouterr()

    assert "policy_exit_code=1" in captured.out
    assert "summary_hint=Potential new secrets detected (1 findings in working tree scan)" in captured.out
