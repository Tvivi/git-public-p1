from pytest_bdd import given, parsers, then, when


@given(parsers.parse("the first number is {value:d}"), target_fixture="first_number")
def given_first_number(value: float) -> float:
    return value


@given(parsers.parse("the second number is {value:d}"), target_fixture="second_number")
def given_second_number(value: float) -> float:
    return value


@when("I add the numbers", target_fixture="result")
def when_add_numbers(first_number: float, second_number: float) -> float:
    return first_number + second_number


@then(parsers.parse("the result should be {expected:d}"))
def then_result_should_be(result: float, expected: float) -> None:
    assert result == expected
