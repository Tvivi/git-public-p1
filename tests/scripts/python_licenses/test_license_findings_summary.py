"""license_findings_summary.py のテスト。"""

from scripts.python_licenses.license_findings_summary import build_summary


def test_build_summary_success() -> None:
    """成功時は問題なしメッセージのみを返す。"""
    summary = build_summary(
        title="All Python license findings (including dev)",
        report_path="artifacts/python-all/pip-licenses-all.json",
        policy_outcome="success",
        dev_scope=True,
    )

    assert "## All Python license findings (including dev)" in summary
    assert "No disallowed licenses detected ✅" in summary
    assert "Fix hints" not in summary


def test_build_summary_failure_for_dev_scope() -> None:
    """失敗時は dev 用ヒントを含む。"""
    summary = build_summary(
        title="All Python license findings (including dev)",
        report_path="artifacts/python-all/pip-licenses-all.json",
        policy_outcome="failure",
        dev_scope=True,
    )

    assert "Disallowed license policy check failed ❌" in summary
    assert "Dev-only packages may be removable" in summary
    assert "Check dependency tree with: `uv tree`" in summary


def test_build_summary_failure_for_prod_scope() -> None:
    """失敗時は本番依存向けヒントを含む。"""
    summary = build_summary(
        title="Production Python license findings",
        report_path="artifacts/python-prod/pip-licenses-prod.json",
        policy_outcome="failure",
        dev_scope=False,
    )

    assert "review redistribution obligations before publishing" in summary
    assert "Dev-only packages may be removable" not in summary
