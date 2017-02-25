# -*- coding: utf-8 -*-
from rete.common import Has, Rule, WME
from rete.network import Network


def init_network():
    net = Network()
    c0 = Has('$x', 'on', '$y')
    c1 = Has('$y', 'left-of', '$z')
    c2 = Has('$z', 'color', 'red')
    net.add_production(Rule(c0, c1, c2))
    return net


def add_wmes():
    net = init_network()
    wmes = [
        WME('B1', 'on', 'B2'),
        WME('B1', 'on', 'B3'),
        WME('B1', 'color', 'red'),
        WME('B2', 'on', 'table'),
        WME('B2', 'left-of', 'B3'),
        WME('B2', 'color', 'blue'),
        WME('B3', 'left-of', 'B4'),
        WME('B3', 'on', 'table'),
        WME('B3', 'color', 'red')
    ]
    for wme in wmes:
        net.add_wme(wme)


def test_init_network(benchmark):
    benchmark(init_network)


def test_add_wmes(benchmark):
    benchmark(add_wmes)
