# -*- coding: utf-8 -*-
from rete.common import Condition as Cond, Var, WME, NCCondition


def test_condition_vars():
    c0 = Cond(Var('x'), 'is', Var('y'))
    assert len(c0.vars) == 2
    assert c0.identifier.field == 'identifier'
    assert c0.identifier.symbol == 'x'
    assert c0.attribute == 'is'


def test_condition_contain():
    c0 = Cond(Var('a'), Var('b'), Var('c'))
    assert c0.contain(Var('a'))
    assert not c0.contain(Var('d'))


def test_condition_test():
    c0 = Cond(Var('x'), 'color', 'red')
    w0 = WME('B1', 'color', 'red')
    w1 = WME('B1', 'color', 'blue')
    assert c0.test(w0)
    assert not c0.test(w1)


def test_ncc():
    c0 = Cond(Var('a'), Var('b'), Var('c'))
    c1 = NCCondition([Cond(Var('x'), 'color', 'red')])
    c2 = NCCondition([c0, c1])
    assert c2.number_of_conditions == 1
