#!/usr/bin/env python
#
# Author: Patrick Hung (patrickh @caltech)
# Author: Mike McKerns (mmckerns @caltech and @uqfoundation)
# Copyright (c) 1997-2016 California Institute of Technology.
# License: 3-clause BSD.  The full license text is available at:
#  - http://trac.mystic.cacr.caltech.edu/project/mystic/browser/mystic/LICENSE
"""
Support Vector Regression. Example 2
"""

from numpy import *
import pylab
from mystic.svr import *

# define the objective function to match standard QP solver
# (see: http://www.mathworks.com/help/optim/ug/quadprog.html)
def objective(x, Q, b):
    return 0.5 * dot(dot(x,Q),x) + dot(b,x)

# define the data points (quadratic data with uniform scatter)
x = arange(-5, 5.001); nx = x.size
y = x*x + 8*random.rand(nx)
N = 2*nx

# build the Kernel Matrix (with custom k)
# get the QP quadratic term
X = concatenate([x,-x])
def pk(a1,a2):
    return (1+a1*a2)*(1+a1*a2)
Q = KernelMatrix(X, pk)
# get the QP linear term
Y = concatenate([y,-y])
svr_epsilon = 4
b = Y + svr_epsilon * ones(Y.size)

# build the constraints (y.T * x = 0.0)
# 1.0*x0 + 1.0*x1 + ... - 1.0*xN = 0.0
Aeq = concatenate([ones(nx), -ones(nx)]).reshape(1,N)
Beq = array([0.])
# set the bounds
lb = zeros(N)
ub = zeros(N) + 0.5

# build the constraints operator
from mystic.symbolic import linear_symbolic, solve, \
     generate_solvers as solvers, generate_constraint as constraint
constrain = linear_symbolic(Aeq,Beq)
constrain = constraint(solvers(solve(constrain,target=['x0'])))

from mystic import suppressed
@suppressed(1e-5)
def conserve(x):
    return constrain(x)

from mystic.monitors import VerboseMonitor
mon = VerboseMonitor(10)

# solve for alpha
from mystic.solvers import diffev
alpha = diffev(objective, zip(lb,.1*ub), args=(Q,b), npop=N*3, gtol=400, \
               itermon=mon, \
               ftol=1e-5, bounds=zip(lb,ub), constraints=conserve, disp=1)

print 'solved x: ', alpha
print "constraint A*x == 0: ", inner(Aeq, alpha)
print "minimum 0.5*x'Qx + b'*x: ", objective(alpha, Q, b)

# calculate support vectors and regression function
sv1 = SupportVectors(alpha[:nx])
sv2 = SupportVectors(alpha[nx:])
R = RegressionFunction(x, y, alpha, svr_epsilon, pk)

print 'support vectors: ', sv1, sv2

# plot data
pylab.plot(x, y, 'k+', markersize=10)

# plot regression function and support
xx = arange(min(x),max(x),0.1)
pylab.plot(xx,R(xx))
pylab.plot(xx,R(xx)-svr_epsilon, 'r--')
pylab.plot(xx,R(xx)+svr_epsilon, 'g--')
pylab.plot(x[sv1],y[sv1],'ro')
pylab.plot(x[sv2],y[sv2],'go')
pylab.show()

# end of file
