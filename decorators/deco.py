from functools import update_wrapper, wraps
from typing import Callable


def disable(func: Callable) -> Callable:
    """
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    >>> memo = disable
    """
    return func


def decorator(decorator_: Callable):

    """
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    """
    @wraps(decorator_)
    def wrapper(func: Callable):
        return update_wrapper(decorator_(func), func)

    return wrapper


@decorator
def count_calls(func: Callable) -> Callable:

    """
    Decorator that counts calls made to the function decorated.
    """

    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        result = func(*args, **kwargs)
        return result
    wrapper.calls = 0

    return wrapper


@decorator
def memo(func: Callable) -> Callable:

    """
    Memoize a function so that it caches all return values for
    faster future lookups.
    """

    cache = dict()

    def wrapper(*args):
        if args in cache:
            return cache[args]
        result = func(*args)
        cache[args] = result

        return result

    return wrapper


@decorator
def n_ary(func: Callable) -> Callable:

    """
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    """

    def wrapper(arg, *args):

        if not args:
            return arg
        return func(arg, wrapper(*args))

    return wrapper


def trace(indent: str):
    """Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    """
    def decorator_(func: Callable):

        @wraps(func)
        def wrapper(*args):
            wrapper.num_calls += 1
            args_as_str = ', '.join(str(arg) for arg in args)
            current_indent = indent * (wrapper.num_calls - 1)
            print(
                f"{current_indent} --> {func.__name__}({args_as_str})"
            )

            result = func(*args)
            print(
                f"{current_indent} <-- {func.__name__}({args_as_str}) == {result}"
            )
            wrapper.num_calls -= 1
            return result
        wrapper.num_calls = 0

        return wrapper

    return decorator_


@memo
@count_calls
@n_ary
def foo(a, b):
    return a + b


@count_calls
@memo
@n_ary
def bar(a, b):
    return a * b


@count_calls
@trace("####")
@memo
def fib(n):
    """Some doc"""
    return 1 if n <= 1 else fib(n-1) + fib(n-2)


def main():
    print(foo(4, 3))
    print(foo(4, 3, 2))
    print(foo(4, 3))
    print("foo was called", foo.calls, "times")

    print(bar(4, 3))
    print(bar(4, 3, 2))
    print(bar(4, 3, 2, 1))
    print("bar was called", bar.calls, "times")

    print(fib.__doc__)
    fib(3)
    print(fib.calls, 'calls made')


if __name__ == '__main__':
    main()
