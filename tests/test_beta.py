# -*- coding: utf-8 -*-

from rete.common import Rule, Has, Neg, WME, Token, Ncc
from rete.network import Network
from rete.pnode import PNode


def test_network_case0():
    net = Network()
    c0 = Has('x', 'id', '1')
    c1 = Has('x', 'kind', '8')
    p0 = net.add_production(Rule(c0, c1))

    w0 = WME('x', 'id', '1')
    w1 = WME('x', 'kind', '8')

    net.add_wme(w0)
    assert not p0.items

    net.remove_wme(w0)
    net.add_wme(w1)
    assert not p0.items

    net.add_wme(w0)
    net.add_wme(w1)
    assert p0.items


def test_network_case1():
    # setup
    net = Network()
    c0 = Has('$x', 'on', '$y')
    c1 = Has('$y', 'left-of', '$z')
    c2 = Has('$z', 'color', 'red')
    net.add_production(Rule(c0, c1, c2))
    # end

    am0 = net.build_or_share_alpha_memory(c0)
    am1 = net.build_or_share_alpha_memory(c1)
    am2 = net.build_or_share_alpha_memory(c2)
    dummy_join = am0.successors[0]
    join_on_value_y = am1.successors[0]
    join_on_value_z = am2.successors[0]
    match_c0 = dummy_join.children[0]
    match_c0c1 = join_on_value_y.children[0]
    match_c0c1c2 = join_on_value_z.children[0]

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

    assert am0.items == [wmes[0], wmes[1], wmes[3], wmes[7]]
    assert am1.items == [wmes[4], wmes[6]]
    assert am2.items == [wmes[2], wmes[8]]
    assert len(match_c0.items) == 4
    assert len(match_c0c1.items) == 2
    assert len(match_c0c1c2.items) == 1

    t0 = Token(Token(None, None), wmes[0])
    t1 = Token(t0, wmes[4])
    t2 = Token(t1, wmes[8])
    assert match_c0c1c2.items[0] == t2

    net.remove_wme(wmes[0])
    assert am0.items == [wmes[1], wmes[3], wmes[7]]
    assert len(match_c0.items) == 3
    assert len(match_c0c1.items) == 1
    assert len(match_c0c1c2.items) == 0


def test_dup():
    # setup
    net = Network()
    c0 = Has('$x', 'self', '$y')
    c1 = Has('$x', 'color', 'red')
    c2 = Has('$y', 'color', 'red')
    net.add_production(Rule(c0, c1, c2))

    wmes = [
        WME('B1', 'self', 'B1'),
        WME('B1', 'color', 'red'),
    ]
    for wme in wmes:
        net.add_wme(wme)
    # end

    am = net.build_or_share_alpha_memory(c2)
    join_on_value_y = am.successors[1]
    match_for_all = join_on_value_y.children[0]

    assert len(match_for_all.items) == 1


def test_negative_condition():
    # setup
    net = Network()
    c0 = Has('$x', 'on', '$y')
    c1 = Has('$y', 'left-of', '$z')
    c2 = Neg('$z', 'color', 'red')
    p0 = net.add_production(Rule(c0, c1, c2))
    # end

    wmes = [
        WME('B1', 'on', 'B2'),
        WME('B1', 'on', 'B3'),
        WME('B1', 'color', 'red'),
        WME('B2', 'on', 'table'),
        WME('B2', 'left-of', 'B3'),
        WME('B2', 'color', 'blue'),
        WME('B3', 'left-of', 'B4'),
        WME('B3', 'on', 'table'),
        WME('B3', 'color', 'red'),
    ]
    for wme in wmes:
        net.add_wme(wme)
    assert p0.items[0].wmes == [
        WME('B1', 'on', 'B3'),
        WME('B3', 'left-of', 'B4'),
        None
    ]


def test_multi_productions():
    net = Network()
    c0 = Has('$x', 'on', '$y')
    c1 = Has('$y', 'left-of', '$z')
    c2 = Has('$z', 'color', 'red')
    c3 = Has('$z', 'on', 'table')
    c4 = Has('$z', 'left-of', 'B4')

    p0 = net.add_production(Rule(c0, c1, c2))
    p1 = net.add_production(Rule(c0, c1, c3, c4))

    wmes = [
        WME('B1', 'on', 'B2'),
        WME('B1', 'on', 'B3'),
        WME('B1', 'color', 'red'),
        WME('B2', 'on', 'table'),
        WME('B2', 'left-of', 'B3'),
        WME('B2', 'color', 'blue'),
        WME('B3', 'left-of', 'B4'),
        WME('B3', 'on', 'table'),
        WME('B3', 'color', 'red'),
    ]
    for wme in wmes:
        net.add_wme(wme)

    # add product on the fly
    p2 = net.add_production(Rule(c0, c1, c3, c2))

    assert len(p0.items) == 1
    assert len(p1.items) == 1
    assert len(p2.items) == 1
    assert p0.items[0].wmes == [wmes[0], wmes[4], wmes[8]]
    assert p1.items[0].wmes == [wmes[0], wmes[4], wmes[7], wmes[6]]
    assert p2.items[0].wmes == [wmes[0], wmes[4], wmes[7], wmes[8]]

    net.remove_production(p2)
    assert len(p2.items) == 0


def test_ncc():
    net = Network()
    c0 = Has('$x', 'on', '$y')
    c1 = Has('$y', 'left-of', '$z')
    c2 = Has('$z', 'color', 'red')
    c3 = Has('$z', 'on', '$w')

    p0 = net.add_production(Rule(c0, c1, Ncc(c2, c3)))
    wmes = [
        WME('B1', 'on', 'B2'),
        WME('B1', 'on', 'B3'),
        WME('B1', 'color', 'red'),
        WME('B2', 'on', 'table'),
        WME('B2', 'left-of', 'B3'),
        WME('B2', 'color', 'blue'),
        WME('B3', 'left-of', 'B4'),
        WME('B3', 'on', 'table'),
    ]
    for wme in wmes:
        net.add_wme(wme)
    assert len(p0.items) == 2
    net.add_wme(WME('B3', 'color', 'red'))
    assert len(p0.items) == 1


def test_black_white():
    net = Network()
    c1 = Has('$item', 'cat', '$cid')
    c2 = Has('$item', 'shop', '$sid')
    white = Ncc(
        Neg('$item', 'cat', '100'),
        Neg('$item', 'cat', '101'),
        Neg('$item', 'cat', '102'),
    )
    n1 = Neg('$item', 'shop', '1')
    n2 = Neg('$item', 'shop', '2')
    n3 = Neg('$item', 'shop', '3')
    p0 = net.add_production(Rule(c1, c2, white, n1, n2, n3))
    wmes = [
        WME('item:1', 'cat', '101'),
        WME('item:1', 'shop', '4'),
        WME('item:2', 'cat', '100'),
        WME('item:2', 'shop', '1'),
    ]
    for wme in wmes:
        net.add_wme(wme)

    assert len(p0.items) == 1
    assert p0.items[0].get_binding('$item') == 'item:1'
