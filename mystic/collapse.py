#!/usr/bin/env python
#
# Author: Mike McKerns (mmckerns @caltech and @uqfoundation)
# Author: Lan Huong Nguyen (lanhuong @stanford)
# Copyright (c) 2012-2015 California Institute of Technology.
# License: 3-clause BSD.  The full license text is available at:
#  - http://trac.mystic.cacr.caltech.edu/project/mystic/browser/mystic/LICENSE

import mystic.monitors as _m

##### collapse detectors #####
def collapse_at(stepmon, target=None, tolerance=0.005, \
                         generations=50, mask=None):
    '''return a set of indices where the parameters exhibit a dimensional
    collapse at the specified target. Dimensional collapse is defined by:
    change(param[i]) <= tolerance over N generations, where:
    change(param[i]) = max(param[i]) - min(param[i]) if target = None, or
    change(param[i]) = abs(param[i] - target) otherwise.

    target can be None, a single value, or a list of values of param length

    collapse will be ignored at any indices specififed in the mask
    '''
    np = _m.numpy
    # reject bad masks
    if mask is None: pass
    elif type(mask) is set:
        for i in mask:
            if hasattr(i, '__len__'):
                msg = "bad element '%s' in mask" % str(i)
                raise ValueError(msg)
    else:
        msg = "%s is not a valid mask" % str(mask)
        raise TypeError(msg)
    # is max distance from target less than tolerance across all generations?
    tolerance = np.asarray(tolerance)
    tolerance.shape = (-1,1)
    params = _m._solutions(stepmon, generations)
    if target is None: params = params.ptp(axis=0) <= tolerance
    else: params = abs(params - target).max(axis=0) <= tolerance
    # get tuple of indices of where collapsed
    params = np.where(params)[-1]
    # apply mask
    if mask is None: return set(params)
    mask = set(mask)
    return set(i for i in params if i not in mask)


def collapse_as(stepmon, offset=False, tolerance=0.005, \
                         generations=50, mask=None):
    '''return a set of pairs of indices where the parameters exhibit a
    dimensional collapse. Dimensional collapse is defined by:
    max(pairwise(parameters)) <= tolerance over N generations (offset=False),
    ptp(pairwise(parameters)) <= tolerance over N generations (offset=True).

    collapse will be ignored at any pairs of indices specififed in the mask.
    If single indices are provided, ignore all pairs with the given indices.
    '''
    np = _m.numpy
    # reject bad masks
    if mask is None: pass
    elif type(mask) is set:
        for i in mask:
            if hasattr(i, '__len__') and len(i) != 2:
                msg = "bad element '%s' in mask" % str(i)
                raise ValueError(msg)
    else:
        msg = "%s is not a valid mask" % str(mask)
        raise TypeError(msg)
    # is the max position difference less than tolerance across all generations?
    distances = _m._solutions(stepmon, generations)
    #FIXME: HACK: array should be ndim=2... apparently sometimes it's ndim=3
    if distances.ndim == 3 and distances.shape[-1] == 1:
        distances.shape = distances.shape[:-1]
    elif distances.ndim < 3:
        pass
    else:
        msg = 'could not extract pairwise distances from array with shape %s' % distances.shape
        raise ValueError(msg) 
    nindices = distances.shape[-1]
    # get distances and pairs of indices
    from mystic.tools import pairwise
    distances, pairs = pairwise(distances, True)
    if offset: # tracking at a distance
        distances = distances.ptp(axis=0) <= tolerance
    else: # tracking with the same position
        distances = distances.max(axis=0) <= tolerance
    # get the (index1,index2) pairs where the collapse occurs
    if distances.ndim > 1:
        distances.shape = tuple(i for i in distances.shape if i != 1) or (1,)
    distances = np.array(pairs)[distances]
    # apply mask
    if mask is None: return set(tuple(i) for i in distances)
    mask = selector(mask)
    return set(tuple(i) for i in distances if not mask(i))


def collapse_weight(stepmon, tolerance=0.005, generations=50, mask=None):
    '''return a dict of {measure:indices} where the product_measure
    exhibits a dimensional collapse in weight. Dimensional collapse in
    weight is defined by: max(weight[i]) <= tolerance over N generations.

    collapse will be ignored at (measure,indices) as specified in the mask.
    Format of mask will determine the return value for this function.  Default
    mask format is dict of {measure: indices}, with alternate formatting
    available as a set of tuples of (measure,index).
    ''' #XXX: not mentioned, 'where' format also available
    np = _m.numpy
    # reject bad masks
    if mask is None: pass
    elif type(mask) is set:
        for i in mask:
            if not hasattr(i, '__len__') or len(i) != 2:
                msg = "bad element '%s' in mask" % str(i)
                raise ValueError(msg)
            if type(i[0]) is not int or type(i[1]) is not int:
                msg = "bad element '%s' in mask" % str(i)
                raise ValueError(msg)
    elif type(mask) is dict:
        for (i,j) in mask.iteritems():
            if type(j) is not set or type(i) is not int:
                msg = "bad entry '%s:%s' in mask" % (str(i),str(j))
                raise ValueError(msg)
            for k in j: # items in the set
                if hasattr(k, '__len__'):
                    msg = "bad entry '%s:%s' in mask" % (str(i),str(j))
                    raise ValueError(msg)
    elif hasattr(mask, '__len__') and len(mask) == 2:
        if np.array(mask).ndim != 2:
            msg = "%s is not a valid mask" % str(mask)
            raise TypeError(msg)
    elif hasattr(mask, '__len__') and not len(mask):
        mask = type(mask)(((),())) #XXX: HACK to get empty where mask
    else:
        msg = "%s is not a valid mask" % str(mask)
        raise TypeError(msg)
    # is the max weight less than tolerance across all generations?
    weights = _m._weights(stepmon, generations).max(axis=0) <= tolerance
    # identify mask format and build filter
    mask, pairs = _weight_filter(mask)
    # get weight collapse in 'where' notation
    wts = (tuple(i) for i in np.where(weights) if len(i))
    # apply mask and selected format...
    if pairs: # return explicit 'pairs' {(measure,index)}
        import itertools as it
        return mask(set(it.izip(*wts)))
    if pairs is None: # return 'where' format [measures,indices]
        return mask(wts)
    # returns a dict of {measure:indices}
    wts = np.array(tuple(wts))
    if not wts.size: return {}
    return mask(dict((i,set(wts[1][wts[0]==i])) for i in range(1+wts[0][-1]) if i in wts[0]))


def collapse_position(stepmon, tolerance=0.005, generations=50, mask=None):
    '''return a dict of {measure: pairs_of_indices} where the product_measure
    exhibits a dimensional collapse in position. Dimensional collapse in
    position is defined by:

    collapse will be ignored at (measure,pairs) as specified in the mask.
    Format of mask will determine the return value for this function.  Default
    mask format is dict of {measure: pairs_of_indices}, with alternate
    formatting available as a set of tuples of (measure,pair).
    ''' #XXX: not mentioned, 'where' format also available
    np = _m.numpy
    # reject bad masks
    if mask is None: pass
    elif type(mask) is set:
        for i in mask:
            if not hasattr(i, '__len__') or len(i) != 2:
                msg = "bad element '%s' in mask" % str(i)
                raise ValueError(msg)
            if type(i[0]) is not int:
                msg = "bad element '%s' in mask" % str(i)
                raise ValueError(msg)
            if np.array(i[1]).ndim != 1:
                msg = "bad element '%s' in mask" % str(i)
                raise ValueError(msg)
    elif type(mask) is dict:
        for (i,j) in mask.iteritems():
            if type(j) is not set or type(i) is not int:
                msg = "bad entry '%s:%s' in mask" % (str(i),str(j))
                raise ValueError(msg)
            for k in j: # items in the set
                if not hasattr(k, '__len__') or len(k) != 2:
                    msg = "bad entry '%s:%s' in mask" % (str(i),str(j))
                    raise ValueError(msg)
    elif hasattr(mask, '__len__') and len(mask) == 2:
        if np.array(mask[0]).ndim != 1:
            msg = "%s is not a valid mask" % str(mask)
            raise TypeError(msg)
        if np.array(mask[1]).ndim != 2:
            msg = "%s is not a valid mask" % str(mask)
            raise TypeError(msg)
    elif hasattr(mask, '__len__') and not len(mask):
        mask = type(mask)(((),())) #XXX: HACK to get empty where mask
    else:
        msg = "%s is not a valid mask" % str(mask)
        raise TypeError(msg)
    # is the max position difference less than tolerance across all generations?
    distances = _m._positions(stepmon, generations)
    nindices = distances.shape[-1]
    from mystic.tools import pairwise
    distances, pairs = pairwise(distances, True)
    distances = distances.max(axis=0) <= tolerance
    # select off the desired pairs (of indices)
    counts = np.cumsum(distances.sum(axis=-1))
    import warnings
    with warnings.catch_warnings():  #FIXME: python2.5
        warnings.simplefilter('ignore')
        #XXX: throws a FutureWarning
        distances = np.split(np.array((pairs,)*distances.shape[0])[distances], counts)[:-1]
    counts = (set(tuple(i) for i in j) for j in distances)
    # return in terms of pairs, b/c indexing alone doesn't give pairings
    # (keys are measure, and values are (index1,index2) pairs)
    distances = ((i,j) for (i,j) in enumerate(counts) if len(j))
    # identify mask format and build filter
    select, pairs = _position_filter(mask)
    # convert to selected format...
    if pairs: # return explicit 'pairs' {(measure,indices)}
        import itertools as it
        mask = set()
        for i,j in distances:
            [mask.add(k) for k in it.izip(*((i,)*len(j), j))]
    elif pairs is None: # return 'where' format [measures,indices]
        import itertools as it
        # tuple of where,pairs
        measures,mask = (),()
        for (i,j) in (zip(*((j[0],i) for i in j[1])) for j in distances):
            measures += i
            mask += j
        mask = (measures,mask) if len(measures) else ()
    else:
        # returns a dict of {measure, indices}
        mask = dict(distances)
    # apply mask
    return select(mask)


##### selectors #####
def _split_mask(mask):
    '''separate a mask into a list of ints and list of tuples (pairs).
    mask should be composed of indices and pairs of indices'''
    tuples = []
    return [i for i in mask if type(i) is int or tuples.append(i)], tuples

def _pair_selector(mask):
    '''generate a selector for a mask of tuples (pairs)'''
    # assume a sequence of pairs is given, exactly specifying the pairs
    from mystic.tools import _inverted
    return lambda x: (tuple(x) in mask or tuple(x) in _inverted(mask))

def _index_selector(mask):
    '''generate a selector for a mask of indices'''
    # assume a sequence of indices is given, specifying one member of a pair
    # all pairs where this index appears are valid
    return lambda x: (int(x[0]) in mask or int(x[1]) in mask)
    
def selector(mask):
    '''generate a selector for a mask of pairs and/or indices'''
    indices, pairs = _split_mask(mask)
    return lambda x: (_pair_selector(pairs)(x) or _index_selector(indices)(x))

def _weight_filter(mask):
    '''generate a filter for a weight mask (dict, set, or where)'''
    if mask is None:
        pairs = False # the default format
        selector = lambda x: x
    elif type(mask) is set:
        pairs = True
        selector = lambda x: x - mask
    elif type(mask) is dict:
        pairs = False
        selector = lambda x: dict((k,v) for (k,v) in ((i,j - mask.get(i,set())) for (i,j) in x.iteritems()) if v)
    else:
        import itertools as it
        pairs = None #XXX: special case, use where notation
        selector = lambda x: tuple(it.izip(*(i for i in it.izip(*x) if i not in it.izip(*mask)))) #FIXME: searching set would be faster
    return selector, pairs

def _position_filter(mask):
    '''generate a filter for a position mask (dict, set, or where)'''
    if mask is None:
        pairs = False # the default format
        selector = lambda x: x
    elif type(mask) is set:
        import itertools as it
        if mask:
            from mystic.tools import _inverted
            _mask,pairs = it.izip(*mask)
            _mask = set(it.izip(_mask,_inverted(pairs)))
        else: _mask = mask
        pairs = True
        selector = lambda x: x - mask - _mask
    elif type(mask) is dict:
        pairs = False
        from mystic.tools import _symmetric
        selector = lambda x: dict((k,v) for (k,v) in ((i,j - _symmetric(mask.get(i,set()))) for (i,j) in x.iteritems()) if v)
    else:
        import itertools as it
        from mystic.tools import _inverted
        _mask,pairs = mask
        mask = _mask+_mask, tuple(pairs)+tuple(_inverted(pairs))
        pairs = None #XXX: special case, use where notation
        selector = lambda x: tuple(it.izip(*(i for i in it.izip(*x) if i not in it.izip(*mask)))) #FIXME: searching set would be faster
    return selector, pairs


##### below require message from message=condition(solver, True) #####
def collapsed(message): #FIXME: more secure if takes condition, not message
    '''extract collapse result from collapse message'''
    #NOTE: keys should match term.__doc__; values are collapses in mask format
    collapses = {}
    for message in message.split('; '):
        message = message.rsplit(' at ',1)
        msg = message.pop(-1)
        if message: collapses[message[0]] = eval(msg)
    return collapses if collapses else None


# from mystic.termination import Or
# from mystic.termination import ChangeOverGeneration as COG

# def combine_termination(*conditions):
#     # stop: configured stop condition
#     # weight: configured weight collapse
#     # position: configured position collapse
#     return Or(*conditions)


#########################################
# {iter: term_msg} and update_constraints
#########################################
##### constraint updaters #####


#########################################
# CollapseAt(None, mask): "max(x[i]) - min(x[i]) < tolerance"
# CollapseAt(target, mask): "abs(x[i] - target) < tolerance"
# CollapseAs(offset, mask): "max(pairwise(x)) < tolerance"
# CollapseWeight(mask): "weights < tolerance"
# CollapsePosition(mask): "max(pairwise(positions)) < tolerance"
#########################################
# 'impose_support': given 'index' w/ support, set other weights = 0.0
#                   ( set to zero?  normalize?  other considerations? )
#                   ( constraints.discrete([0], index=(collapsed params)) )?
#                   ( tools.synchronized({p:(-1,lambda x:0)}) )?
#                   ( option to normalize or not? )
# 'impose_collapse': given dict of collapse, sync positions (& remove support?)
#                   ( random.choice to zero weight, increase the other weight )
#                   ( synchronize position with other position )
#                   ( tools.synchronized({p1:(p2,lambda x:x+offset)}) )?
#                   ( option to reweight or not? option to normalize or not? )
# 'impose_target': ==> xi at (target); target is float or list (of floats)
# 'impose_offset': ==> xi at (xj+offset)


# EOF
