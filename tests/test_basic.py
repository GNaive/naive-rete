# -*- coding: utf-8 -*-
from rete import Condition as Cond, Var


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
