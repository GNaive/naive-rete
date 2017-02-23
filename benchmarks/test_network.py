# -*- coding: utf-8 -*-
from rete.common import Condition as Cond, WME
from rete.network import Network


def init_network():
    net = Network()
    c0 = Cond('$x', 'on', '$y')
    c1 = Cond('$y', 'left-of', '$z')
    c2 = Cond('$z', 'color', 'red')
    net.add_production([c0, c1, c2])
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
