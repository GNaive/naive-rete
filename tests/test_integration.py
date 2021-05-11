# -*- coding: utf-8 -*-
from rete.network import Network, Rule
from rete.common import Has, WME


def test_binding_should_not_match():

    net = Network()
    c0 = Has('foo', '$x', '$x')
    p0 = net.add_production(Rule(c0))
    net.add_wme(WME('foo', 'bar', 'baz'))

    assert len(p0.items) == 0


def test_should_match_one():

    net = Network()
    c0 = Has('foo', '$x', '$x')
    p0 = net.add_production(Rule(c0))
    net.add_wme(WME('foo', 'quux', 'quux'))

    assert len(p0.items) == 1


def test_all_variables():

    net = Network()
    c0 = Has('$x', '$y', '$y')
    p0 = net.add_production(Rule(c0))
    net.add_wme(WME('foo', 'bar', 'baz'))

    assert len(p0.items) == 0


def test_all_variables_the_same_should_match():

    net = Network()
    c0 = Has('$x', '$x', '$x')
    p0 = net.add_production(Rule(c0))
    net.add_wme(WME('foo', 'foo', 'foo'))

    assert len(p0.items) == 1


def test_all_variables_the_same_should_not_match():

    net = Network()
    c0 = Has('$x', '$x', '$x')
    p0 = net.add_production(Rule(c0))
    net.add_wme(WME('bar', 'foo', 'foo'))

    assert len(p0.items) == 0


def test_all_constants_the_same_should_match_one():

    net = Network()
    c0 = Has('foo', 'foo', 'foo')
    p0 = net.add_production(Rule(c0))
    net.add_wme(WME('foo', 'foo', 'foo'))

    assert len(p0.items) == 1


def test_all_constants_the_same_should_not_match():

    net = Network()
    c0 = Has('foo', 'foo', 'foo')
    p0 = net.add_production(Rule(c0))
    net.add_wme(WME('bar', 'foo', 'foo'))

    assert len(p0.items) == 0


def test_multiple_conditions_should_match_one():

    net = Network()
    c0 = Has('foo', '$x', '$y')
    c1 = Has('$x', '$x', '$y')
    c2 = Has('$x', 'foo', 'baz')
    p0 = net.add_production(Rule(c0, c1, c2))
    net.add_wme(WME('foo', 'foo', 'baz'))

    assert len(p0.items) == 1


def test_multiple_conditions_should_not_match():

    net = Network()
    c0 = Has('foo', '$x', '$y')
    c1 = Has('foo', '$x', '$x')
    c2 = Has('$x', '$y', 'baz')
    p0 = net.add_production(Rule(c0, c1, c2))
    net.add_wme(WME('foo', 'bar', 'baz'))

    assert len(p0.items) == 0


def test_multiple_conditions_all_variables_should_match_one():

    net = Network()
    c0 = Has('foo', 'foo', 'foo')
    c1 = Has('$x', '$x', '$x')
    c2 = Has('$x', 'foo', 'foo')
    c3 = Has('foo', '$x', 'foo')
    c4 = Has('$x', 'foo', '$x')
    p0 = net.add_production(Rule(c0, c1, c2, c3, c4))
    net.add_wme(WME('foo', 'foo', 'foo'))

    assert len(p0.items) == 1


def test_multiple_conditions_all_variables_should_match_one_2():

    net = Network()
    c0 = Has('$x', '$x', '$x')
    c1 = Has('foo', '$x', 'foo')
    p0 = net.add_production(Rule(c0, c1))
    net.add_wme(WME('foo', 'foo', 'foo'))

    assert len(p0.items) == 1
