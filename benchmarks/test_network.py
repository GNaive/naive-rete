# -*- coding: utf-8 -*-
from rete import Network, Condition as Cond, Var


def init_network():
    net = Network()
    c0 = Cond(Var('x'), 'on', Var('y'))
    c1 = Cond(Var('y'), 'left-of', Var('z'))
    c2 = Cond(Var('z'), 'color', 'red')
    return net.add_production([c0, c1, c2])


def test_init_network(benchmark):
    assert benchmark(init_network)
