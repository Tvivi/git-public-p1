Feature: Calculator
  Simple calculator behavior

  Scenario: Add two numbers
    Given the first number is 2
    And the second number is 3
    When I add the numbers
    Then the result should be 5

  Scenario Outline: Add multiple patterns
    Given the first number is <a>
    And the second number is <b>
    When I add the numbers
    Then the result should be <result>

    Examples:
      | a | b | result |
      | 1 | 2 | 3      |
      | 5 | 7 | 12     |
