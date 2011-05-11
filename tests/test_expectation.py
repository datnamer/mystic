#! /usr/bin/env python
"""
test imposing the expectation for a function f by optimization
"""
debug = True

from math import pi, cos, tanh
import random

def ballistic_limit(h,a):
  """calculate ballistic limit

  Inputs:
    - h = thickness
    - a = obliquity

  Outputs:
    - v_bl = velocity (ballistic limit)
"""
 #assumes h,a have been scaled:
 #h = x[0] * 25.4 * 1e-3
 #a = x[1] * pi/180.0
  Ho = 0.5794
  s = 1.4004
  n = 0.4482
  return Ho * ( h / cos(a)**n )**s

def marc_surr(x):
  """calculate perforation area using a tanh-based model surrogate

  Inputs:
    - x = [thickness, obliquity, speed]

  Outputs:
    - A = perforation area
"""
# h = thickness = [60,105]
# a = obliquity = [0,30]
# v = speed = [2.1,2.8]
  h = x[0] * 25.4 * 1e-3
  a = x[1] * pi/180.0
  v = x[2]

  K = 10.3963
  p = 0.4757
  u = 1.0275
  m = 0.4682
  Dp = 1.778

  # compare to ballistic limit
  v_bl = ballistic_limit(h,a)
  if v < v_bl:
    return 0.0

  return K * (h/Dp)**p * (cos(a))**u * (tanh((v/v_bl)-1))**m


if __name__ == '__main__':
  G = marc_surr  #XXX: uses the above-provided test function
  function_name = G.__name__

  _mean = 06.0   #NOTE: SET THE mean HERE!
  _range = 00.5  #NOTE: SET THE range HERE!
  nx = 3  #NOTE: SET THE NUMBER OF 'h' POINTS HERE!
  ny = 3  #NOTE: SET THE NUMBER OF 'a' POINTS HERE!
  nz = 3  #NOTE: SET THE NUMBER OF 'v' POINTS HERE!

  h_lower = [60.0];  a_lower = [0.0];  v_lower = [2.1]
  h_upper = [105.0]; a_upper = [30.0]; v_upper = [2.8]

  lower_bounds = (nx * h_lower) + (ny * a_lower) + (nz * v_lower)
  upper_bounds = (nx * h_upper) + (ny * a_upper) + (nz * v_upper)
  bounds = (lower_bounds,upper_bounds)

  print " model: f(x) = %s(x)" % function_name
  print " mean: %s" % _mean
  print " range: %s" % _range
  print "..............\n"

  if debug:
    param_string = "["
    for i in range(nx):
      param_string += "'x%s', " % str(i+1)
    for i in range(ny):
      param_string += "'y%s', " % str(i+1)
    for i in range(nz):
      param_string += "'z%s', " % str(i+1)
    param_string = param_string[:-2] + "]"

    print " parameters: %s" % param_string
    print " lower bounds: %s" % lower_bounds
    print " upper bounds: %s" % upper_bounds
  # print " ..."

  wx = [1.0 / float(nx)] * nx
  wy = [1.0 / float(ny)] * ny
  wz = [1.0 / float(nz)] * nz

  from mystic.math.measures import _pack, _unpack
  wts = _pack([wx,wy,wz])
  weights = [i[0]*i[1]*i[2] for i in wts]

  if not debug:
    constraints = None
  else:  # impose a mean constraint on 'thickness'
    h_mean = (h_upper[0] + h_lower[0]) / 2.0
    h_error = 1.0
    v_mean = (v_upper[0] + v_lower[0]) / 2.0
    v_error = 0.05
    print "impose: mean[x] = %s +/- %s" % (str(h_mean),str(h_error))
    print "impose: mean[z] = %s +/- %s" % (str(v_mean),str(v_error))
    def constraints(x, w):
      from mystic.math.dirac_measure import compose, decompose
      c = compose(x,w)
      E = float(c[0].mean)
      if not (E <= float(h_mean+h_error)) or not (float(h_mean-h_error) <= E):
        c[0].mean = h_mean
      E = float(c[2].mean)
      if not (E <= float(v_mean+v_error)) or not (float(v_mean-v_error) <= E):
        c[2].mean = v_mean
      return decompose(c)[0]

  from mystic.math.measures import mean, expectation, impose_expectation
  samples = impose_expectation((_mean,_range), G, (nx,ny,nz), bounds, \
                                      weights, constraints=constraints)

  if debug:
    from numpy import array
    # rv = [xi]*nx + [yi]*ny + [zi]*nz
    smp = _unpack(samples,(nx,ny,nz))
    print "\nsolved [x]: %s" % array( smp[0] )
    print "solved [y]: %s" % array( smp[1] )
    print "solved [z]: %s" % array( smp[2] )
    #print "solved: %s" % smp
    print "\nmean[x]: %s" % mean(smp[0])  # weights are all equal
    print "mean[y]: %s" % mean(smp[1])  # weights are all equal
    print "mean[z]: %s\n" % mean(smp[2])  # weights are all equal

  Ex = expectation(G, samples, weights)
  print "expect: %s" % Ex
  print "cost = (E[G] - m)^2: %s" % (Ex - _mean)**2

# EOF