# -*- coding: utf-8 -*-
from rete.common import Condition as Cond, WME, NCCondition


def test_condition_vars():
    c0 = Cond('$x', 'is', '$y')
    assert len(c0.vars) == 2


def test_condition_contain():
    c0 = Cond('$a', '$b', '$c')
    assert c0.contain('$a')
    assert not c0.contain('$d')


def test_condition_test():
    c0 = Cond('$x', 'color', 'red')
    w0 = WME('B1', 'color', 'red')
    w1 = WME('B1', 'color', 'blue')
    assert c0.test(w0)
    assert not c0.test(w1)


def test_ncc():
    c0 = Cond('$a', '$b', '$c')
    c1 = NCCondition([Cond('$x', 'color', 'red')])
    c2 = NCCondition([c0, c1])
    assert c2.number_of_conditions == 1
