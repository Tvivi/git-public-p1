"""
build_security_report_index.py のユニットテスト。

テスト対象：
- テキスト読み込み
- 索引Markdown生成
"""

from __future__ import annotations

from pathlib import Path

from scripts.security.build_security_report_index import build_index, load_text


def test_load_text_missing_file(tmp_path: Path) -> None:
    """存在しないファイルは Missing 表記になる。"""
    text = load_text(tmp_path / "missing.md")
    assert "Missing file" in text


def test_build_index_contains_all_sections() -> None:
    """すべてのセクション見出しが含まれる。"""
    text = build_index(
        detect_summary_md="detect",  # pragma: allowlist secret
        gitleaks_summary="gitleaks",
        trivy_config_summary="config",
        trivy_fs_summary="fs",
    )

    assert "# Repository Security Reports" in text
    assert "## detect-secrets" in text
    assert "## Gitleaks" in text
    assert "## Trivy config" in text
    assert "## Trivy fs" in text
