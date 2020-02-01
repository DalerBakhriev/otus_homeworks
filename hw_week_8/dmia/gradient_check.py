import random
from typing import Callable

import numpy as np


def eval_numerical_gradient(f, x):

    """
    a naive implementation of numerical gradient of f at x
    - f should be a function that takes a single argument
    - x is the point (numpy array) to evaluate the gradient at
    """

    fx = f(x)  # evaluate function value at original point
    grad = np.zeros(x.shape)
    h = 0.00001

    # iterate over all indexes in x
    it = np.nditer(x, flags=['multi_index'], op_flags=['readwrite'])
    while not it.finished:
        # evaluate function at x+h
        ix = it.multi_index
        x[ix] += h  # increment by h
        fxh = f(x)  # evalute f(x + h)
        x[ix] -= h  # restore to previous value (very important!)

        # compute the partial derivative
        grad[ix] = (fxh - fx) / h  # the slope
        print(ix, grad[ix])
        it.iternext()  # step to next dimension
    return grad


def grad_check_sparse(f: Callable,
                      x: np.ndarray,
                      analytic_grad: np.ndarray,
                      num_checks: int):

    """
    sample a few random elements and only return numerical
    in this dimensions.
    """
    h = 1e-5

    for i in range(num_checks):
        ix = tuple([random.randrange(m) for m in x.shape])

        x[ix] += h  # increment by h
        f_x_plus_h = f(x)  # evaluate f(x + h)
        x[ix] -= 2 * h  # increment by h
        f_x_minus_h = f(x)  # evaluate f(x - h)
        x[ix] += h  # reset

        grad_numerical = (f_x_plus_h - f_x_minus_h) / (2 * h)
        grad_analytic = analytic_grad[ix]
        rel_error = abs(grad_numerical - grad_analytic) / (abs(grad_numerical) + abs(grad_analytic))
        print(f"numerical: {grad_numerical} analytic: {grad_analytic}, relative error: {rel_error}")
