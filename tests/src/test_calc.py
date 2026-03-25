import pytest

from calc_app.calc import add, div, mul, sub


def test_add() -> None:
    assert add(2, 3) == 5


def test_sub() -> None:
    assert sub(5, 3) == 2


def test_mul() -> None:
    assert mul(4, 3) == 12


def test_div() -> None:
    assert div(10, 2) == 5


def test_div_zero() -> None:
    with pytest.raises(ValueError, match="division by zero"):
        div(10, 0)
