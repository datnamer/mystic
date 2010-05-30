#!/usr/bin/env python
""" NOTE:
rosen rewritten as a pickleable function
"""

def rosen(coeffs):
    """evaluates n-dimensional Rosenbrock function for a list of coeffs

minimum is f(x)=0.0 at xi=1.0"""
    from numpy import sum as numpysum
    from numpy import asarray

    #ensure that there are 2 coefficients
    x = [1]*2
    x[:len(coeffs)]=coeffs
    x = asarray(x) #XXX: must be a numpy.array
    return numpysum(100.0*(x[1:]-x[:-1]**2.0)**2.0 + (1-x[:-1])**2.0)


if __name__=='__main__':
    target = [1., 1., 1.]
    print target
    print ""
    print rosen(target)