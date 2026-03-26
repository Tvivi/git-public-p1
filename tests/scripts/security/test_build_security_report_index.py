"""
build_security_report_index.py のユニットテスト。

テスト対象：
- セクション生成
- 索引Markdown生成
- summary 本文を読まずに存在確認だけすること
"""

from __future__ import annotations

from pathlib import Path

from scripts.security.build_security_report_index import (
    build_index,
    build_section,
)


def test_build_section_with_existing_file(tmp_path: Path) -> None:
    """存在する summary はファイル名だけを表示する。"""
    summary = tmp_path / "detect-summary.md"
    summary.write_text("Potential secret in a.py", encoding="utf-8")

    text = build_section("detect-secrets", summary)

    assert "## detect-secrets" in text
    assert "detect-summary.md" in text
    assert "Detailed findings are intentionally not embedded" in text
    assert "Potential secret in a.py" not in text


def test_build_section_with_missing_file(tmp_path: Path) -> None:
    """存在しない summary は missing 表記になる。"""
    summary = tmp_path / "missing-summary.md"

    text = build_section("Gitleaks", summary)

    assert "## Gitleaks" in text
    assert "Summary file is missing" in text
    assert "missing-summary.md" in text


def test_build_index_contains_all_sections(tmp_path: Path) -> None:
    """すべてのセクション見出しが含まれる。"""
    detect = tmp_path / "detect.md"
    gitleaks = tmp_path / "gitleaks.md"
    trivy_config = tmp_path / "trivy-config.md"
    trivy_fs = tmp_path / "trivy-fs.md"

    detect.write_text("secret like text", encoding="utf-8")
    gitleaks.write_text("another detail", encoding="utf-8")
    trivy_config.write_text("config detail", encoding="utf-8")
    trivy_fs.write_text("fs detail", encoding="utf-8")

    text = build_index(
        detect_summary_path=detect,
        gitleaks_summary_path=gitleaks,
        trivy_config_summary_path=trivy_config,
        trivy_fs_summary_path=trivy_fs,
    )

    assert "# Repository Security Reports" in text
    assert "## detect-secrets" in text
    assert "## Gitleaks" in text
    assert "## Trivy config" in text
    assert "## Trivy fs" in text


def test_build_index_does_not_embed_summary_contents(tmp_path: Path) -> None:
    """summary に危険そうな文字列があっても index へ再掲しない。"""
    detect = tmp_path / "detect.md"
    gitleaks = tmp_path / "gitleaks.md"
    trivy_config = tmp_path / "trivy-config.md"
    trivy_fs = tmp_path / "trivy-fs.md"

    detect.write_text("Potential secret in a.py", encoding="utf-8")
    gitleaks.write_text("commit: abcdef", encoding="utf-8")
    trivy_config.write_text("HIGH finding", encoding="utf-8")
    trivy_fs.write_text("generic-api-key", encoding="utf-8")

    text = build_index(
        detect_summary_path=detect,
        gitleaks_summary_path=gitleaks,
        trivy_config_summary_path=trivy_config,
        trivy_fs_summary_path=trivy_fs,
    )

    assert "Potential secret in a.py" not in text
    assert "commit: abcdef" not in text
    assert "generic-api-key" not in text
