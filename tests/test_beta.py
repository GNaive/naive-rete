# -*- coding: utf-8 -*-

from rete.common import Condition as Cond, WME, Token, NCCondition as NCC
from rete.network import Network


def test_network_case0():
    net = Network()
    c0 = Cond('x', 'id', '1')
    c1 = Cond('x', 'kind', '8')
    p0 = net.add_production([c0, c1])

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
    c0 = Cond('$x', 'on', '$y')
    c1 = Cond('$y', 'left-of', '$z')
    c2 = Cond('$z', 'color', 'red')
    net.add_production([c0, c1, c2])
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
    c0 = Cond('$x', 'self', '$y')
    c1 = Cond('$x', 'color', 'red')
    c2 = Cond('$y', 'color', 'red')
    net.add_production([c0, c1, c2])

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
    c0 = Cond('$x', 'on', '$y')
    c1 = Cond('$y', 'left-of', '$z')
    c2 = Cond('$z', 'color', 'red', positive=False)
    p0 = net.add_production([c0, c1, c2])
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
    c0 = Cond('$x', 'on', '$y')
    c1 = Cond('$y', 'left-of', '$z')
    c2 = Cond('$z', 'color', 'red')
    c3 = Cond('$z', 'on', 'table')
    c4 = Cond('$z', 'left-of', 'B4')

    p0 = net.add_production([c0, c1, c2])
    p1 = net.add_production([c0, c1, c3, c4])

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
    p2 = net.add_production([c0, c1, c3, c2])

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
    c0 = Cond('$x', 'on', '$y')
    c1 = Cond('$y', 'left-of', '$z')
    c2 = Cond('$z', 'color', 'red')
    c3 = Cond('$z', 'on', '$w')

    p0 = net.add_production([c0, c1, NCC([c2, c3])])
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


def test_compare_op():
    net = Network()
    c0 = Cond('$x', 'amount', '>100')
    c1 = Cond('$x', 'amount', '<200')
    c2 = Cond('$x', 'product_id', '101')

    p0 = net.add_production([c0, c1, c2])
    net.add_wme(WME('order-101', 'amount', '150'))
    net.add_wme(WME('order-101', 'product_id', '101'))
    assert p0.items


def test_compare_op_negative():
    net = Network()
    c0 = Cond('$x', 'amount', '>100')
    c1 = Cond('$x', 'amount', '>200', positive=False)

    p0 = net.add_production([c0, c1])
    w0 = WME('order-101', 'amount', '280')
    net.add_wme(w0)
    assert not p0.items

    net.remove_wme(w0)
    net.add_wme(WME('order-101', 'amount', '150'))
    assert p0.items
