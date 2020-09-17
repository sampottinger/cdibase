import typing


T = typing.TypeVar('T')


def assert_not_none(target: typing.Optional[T]) -> T:
    """Check that a value is not None.

    @param target: The value to test.
    @returns: The same value input if not None. Error thrown if None.
    """
    assert target != None
    return target # type: ignore
