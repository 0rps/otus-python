#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper


def disable(func):
    '''
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    >>> memo = disable

    '''

    return func


def decorator(wrapped):
    '''
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    '''

    def internal_decorator(wrapper):
        update_wrapper(wrapper, wrapped)
        return wrapper

    return internal_decorator


def countcalls(func):
    '''Decorator that counts calls made to the function decorated.'''

    @decorator(func)
    def wrapped(*args, **kwargs):
        wrapped.calls += 1
        return func(*args, **kwargs)
    wrapped.calls = 0
    return wrapped


def memo(func):
    '''
    Memoize a function so that it caches all return values for
    faster future lookups.
    '''
    memory = {}

    @decorator(func)
    def wrapped(*args):
        nonlocal memory
        if args in memory:
            return memory[args]

        result = func(*args)
        memory[args] = result
        return result

    return wrapped


def n_ary(func):
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''

    @decorator(func)
    def wrapped(*args):
        length = len(args)
        if length == 1:
            return args[0]
        elif length > 1:
            return func(args[0], wrapped(*args[1:]))

    return wrapped


def trace(indent_step):
    '''Trace calls made to function decorated.

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

    '''

    def internal_decorator(func):
        indent = ''

        @decorator(func)
        def wrapped(*args, **kwargs):
            nonlocal indent
            old_indent = indent
            indent += indent_step

            func_args = ", ".join([str(x) for x in args])
            func_call = "{}({})".format(func.__name__, func_args)

            print("{} --> {}".format(indent, func_call))
            result = func(*args, **kwargs)
            print("{} <-- {} == {}".format(indent, func_call, result))

            indent = old_indent
            return result

        return wrapped
    return internal_decorator


@countcalls
@memo
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
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
