"""
TestBox-style expectation helpers for pytest.

Provides fluent assertions similar to TestBox's expect() syntax:

    expect(actual).to_be(expected)
    expect(collection).to_contain(item)
    expect(string).to_match(pattern)
    expect(value).to_be_gt(other)
"""

import re
from typing import Any, Optional


class ExpectationFailed(AssertionError):
    """Raised when an expectation fails."""

    def __init__(self, message: str, actual: Any = None, expected: Any = None):
        self.actual = actual
        self.expected = expected
        super().__init__(message)


class Expectation:
    """Fluent expectation object, similar to TestBox's expect()."""

    def __init__(self, actual: Any, negated: bool = False):
        self._actual = actual
        self._negated = negated

    @property
    def not_to(self) -> "Expectation":
        """Negate the next expectation."""
        return Expectation(self._actual, negated=True)

    def _assert(self, condition: bool, message: str, expected: Any = None):
        """Internal assertion helper."""
        if self._negated:
            if condition:
                raise ExpectationFailed(f"Expected NOT {message}", self._actual, expected)
        else:
            if not condition:
                raise ExpectationFailed(f"Expected {message}", self._actual, expected)

    # ─── Identity / Equality ───────────────────────────────────────────

    def to_be(self, expected: Any) -> "Expectation":
        """Expect actual to be equal to expected (==)."""
        self._assert(
            self._actual == expected,
            f"{self._actual!r} to be {expected!r}",
            expected,
        )
        return self

    def to_be_equal(self, expected: Any) -> "Expectation":
        """Alias for to_be."""
        return self.to_be(expected)

    def to_be_same(self, expected: Any) -> "Expectation":
        """Expect actual to be the same object (is)."""
        self._assert(
            self._actual is expected,
            f"{self._actual!r} to be same as {expected!r}",
            expected,
        )
        return self

    def not_to_be(self, expected: Any) -> "Expectation":
        """Expect actual to NOT be equal to expected."""
        return self.not_to.to_be(expected)

    def not_to_start_with(self, prefix: str) -> "Expectation":
        """Expect actual (string) to NOT start with prefix."""
        return self.not_to.to_start_with(prefix)

    def not_to_end_with(self, suffix: str) -> "Expectation":
        """Expect actual (string) to NOT end with suffix."""
        return self.not_to.to_end_with(suffix)

    def not_to_contain_string(self, substring: str) -> "Expectation":
        """Expect actual (string) to NOT contain substring."""
        return self.not_to.to_contain_string(substring)

    # ─── Type ──────────────────────────────────────────────────────────

    def to_be_instance_of(self, expected_type: type) -> "Expectation":
        """Expect actual to be an instance of expected_type."""
        self._assert(
            isinstance(self._actual, expected_type),
            f"{self._actual!r} to be instance of {expected_type.__name__}",
            expected_type,
        )
        return self

    def to_be_a(self, expected_type: type) -> "Expectation":
        """Alias for to_be_instance_of."""
        return self.to_be_instance_of(expected_type)

    # ─── Boolean ───────────────────────────────────────────────────────

    def to_be_true(self) -> "Expectation":
        """Expect actual to be True."""
        self._assert(self._actual is True, f"{self._actual!r} to be True")
        return self

    def to_be_false(self) -> "Expectation":
        """Expect actual to be False."""
        self._assert(self._actual is False, f"{self._actual!r} to be False")
        return self

    # ─── None ──────────────────────────────────────────────────────────

    def to_be_none(self) -> "Expectation":
        """Expect actual to be None."""
        self._assert(self._actual is None, f"{self._actual!r} to be None")
        return self

    def not_to_be_none(self) -> "Expectation":
        """Expect actual to NOT be None."""
        return self.not_to.to_be_none()

    # ─── Collections ───────────────────────────────────────────────────

    def to_contain(self, item: Any) -> "Expectation":
        """Expect actual (collection) to contain item."""
        self._assert(
            item in self._actual,
            f"{self._actual!r} to contain {item!r}",
            item,
        )
        return self

    def not_to_contain(self, item: Any) -> "Expectation":
        """Expect actual (collection) to NOT contain item."""
        return self.not_to.to_contain(item)

    def to_include(self, item: Any) -> "Expectation":
        """Alias for to_contain."""
        return self.to_contain(item)

    def to_have_length(self, length: int) -> "Expectation":
        """Expect actual (collection) to have given length."""
        actual_len = len(self._actual) if hasattr(self._actual, "__len__") else 0
        self._assert(
            actual_len == length,
            f"{self._actual!r} to have length {length}, got {actual_len}",
            length,
        )
        return self

    def to_be_empty(self) -> "Expectation":
        """Expect actual (collection) to be empty."""
        return self.to_have_length(0)

    def not_to_be_empty(self) -> "Expectation":
        """Expect actual (collection) to NOT be empty."""
        return self.not_to.to_be_empty()

    def to_have_key(self, key: Any) -> "Expectation":
        """Expect actual (dict) to have given key."""
        self._assert(
            key in self._actual,
            f"{self._actual!r} to have key {key!r}",
            key,
        )
        return self

    def not_to_have_key(self, key: Any) -> "Expectation":
        """Expect actual (dict) to NOT have given key."""
        return self.not_to.to_have_key(key)

    # ─── Strings ───────────────────────────────────────────────────────

    def to_start_with(self, prefix: str) -> "Expectation":
        """Expect actual (string) to start with prefix."""
        self._assert(
            str(self._actual).startswith(prefix),
            f"{self._actual!r} to start with {prefix!r}",
            prefix,
        )
        return self

    def to_end_with(self, suffix: str) -> "Expectation":
        """Expect actual (string) to end with suffix."""
        self._assert(
            str(self._actual).endswith(suffix),
            f"{self._actual!r} to end with {suffix!r}",
            suffix,
        )
        return self

    def to_contain_string(self, substring: str) -> "Expectation":
        """Expect actual (string) to contain substring."""
        self._assert(
            substring in str(self._actual),
            f"{self._actual!r} to contain {substring!r}",
            substring,
        )
        return self

    def to_match(self, pattern: str) -> "Expectation":
        """Expect actual (string) to match regex pattern."""
        self._assert(
            re.search(pattern, str(self._actual)),
            f"{self._actual!r} to match pattern {pattern!r}",
            pattern,
        )
        return self

    # ─── Numeric ───────────────────────────────────────────────────────

    def to_be_gt(self, other: float) -> "Expectation":
        """Expect actual to be greater than other."""
        self._assert(
            self._actual > other,
            f"{self._actual!r} to be greater than {other!r}",
            other,
        )
        return self

    def to_be_gte(self, other: float) -> "Expectation":
        """Expect actual to be greater than or equal to other."""
        self._assert(
            self._actual >= other,
            f"{self._actual!r} to be >= {other!r}",
            other,
        )
        return self

    def to_be_lt(self, other: float) -> "Expectation":
        """Expect actual to be less than other."""
        self._assert(
            self._actual < other,
            f"{self._actual!r} to be less than {other!r}",
            other,
        )
        return self

    def to_be_lte(self, other: float) -> "Expectation":
        """Expect actual to be less than or equal to other."""
        self._assert(
            self._actual <= other,
            f"{self._actual!r} to be <= {other!r}",
            other,
        )
        return self

    def to_be_close_to(self, other: float, delta: float = 0.001) -> "Expectation":
        """Expect actual to be within delta of other."""
        self._assert(
            abs(self._actual - other) <= delta,
            f"{self._actual!r} to be close to {other!r} (delta={delta})",
            other,
        )
        return self

    # ─── Exceptions ────────────────────────────────────────────────────

    def to_throw(self, exception_type: type = Exception) -> "Expectation":
        """Expect actual (callable) to raise an exception."""
        try:
            self._actual()
            self._assert(False, f"callable to raise {exception_type.__name__}", exception_type)
        except exception_type:
            pass
        return self

    # ─── Truthiness ────────────────────────────────────────────────────

    def to_be_truthy(self) -> "Expectation":
        """Expect actual to be truthy."""
        self._assert(bool(self._actual), f"{self._actual!r} to be truthy")
        return self

    def to_be_falsy(self) -> "Expectation":
        """Expect actual to be falsy."""
        self._assert(not self._actual, f"{self._actual!r} to be falsy")
        return self


def expect(actual: Any) -> Expectation:
    """Create a new expectation, TestBox-style.

    Usage:
        expect(actual).to_be(expected)
        expect(collection).to_contain(item)
        expect(string).to_match(pattern)
        expect(value).not_to_be(expected)
    """
    return Expectation(actual)
