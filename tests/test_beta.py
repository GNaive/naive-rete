# -*- coding: utf-8 -*-

from rete import Condition as Cond, Network, Var, WME, Token


def test_network():
    # setup
    net = Network()
    c0 = Cond(Var('x'), 'on', Var('y'))
    c1 = Cond(Var('y'), 'left-of', Var('z'))
    c2 = Cond(Var('z'), 'color', 'red')
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

    t0 = Token(None, wmes[0])
    t1 = Token(t0, wmes[4])
    t2 = Token(t1, wmes[8])
    assert match_c0c1c2.items[0] == t2


def test_dup():
    # setup
    net = Network()
    c0 = Cond(Var('x'), 'self', Var('y'))
    c1 = Cond(Var('x'), 'color', 'red')
    c2 = Cond(Var('y'), 'color', 'red')
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
