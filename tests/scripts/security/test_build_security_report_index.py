"""
build_security_report_index.py のユニットテスト。

テスト対象：
- テキスト読み込み
- 索引Markdown生成
- 安全なプレビュー生成
"""

from __future__ import annotations

from pathlib import Path

from scripts.security.build_security_report_index import (
    build_index,
    build_section_preview,
    load_text,
)


def test_load_text_missing_file(tmp_path: Path) -> None:
    """存在しないファイルは Missing 表記になる。"""
    text = load_text(tmp_path / "missing.md")
    assert "Missing file" in text


def test_build_section_preview_skips_headings_and_code_blocks() -> None:
    """見出しやコードブロックはプレビューに含めない。"""
    preview = build_section_preview(
        "\n".join(
            [
                "### heading",
                "",
                "- Total findings: **2**",
                "```text",
                "secret-like output",
                "```",
                "- Hint: review baseline",
                "",
            ]
        )
    )

    assert "- Total findings: **2**" in preview
    assert "- - Hint: review baseline" in preview
    assert "secret-like output" not in preview
    assert "### heading" not in preview


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


def test_build_index_does_not_embed_code_block_content() -> None:
    """コードブロック内の内容は index に再掲しない。"""
    text = build_index(
        detect_summary_md="```text\nPotential secret in a.py\n```",
        gitleaks_summary="ok",
        trivy_config_summary="ok",
        trivy_fs_summary="ok",
    )

    assert "Potential secret in a.py" not in text
