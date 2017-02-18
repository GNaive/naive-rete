# -*- coding: utf-8 -*-

import copy
from rete.nodes import (
    ConstantTestNode, AlphaMemory, BetaMemory, Token, FIELDS, Var,
    TestAtJoinNode, JoinNode, NegativeNode, Condition, NCCondition,
    BetaNode, NCCNode, NCCPartnerNode
)


class Network:

    def __init__(self):
        self.alpha_root = ConstantTestNode('no-test', amem=AlphaMemory())
        self.beta_root = BetaNode()

    def add_production(self, lhs):
        """
        :type lhs: list of Condition
        """
        if isinstance(lhs, Condition):
            lhs = [lhs]
        current_node = self.build_or_share_network_for_conditions(self.beta_root, lhs, [])
        return self.build_or_share_beta_memory(current_node)

    def remove_production(self, node):
        self.delete_node_and_any_unused_ancestors(node)

    def add_wme(self, wme):
        self.alpha_root.activation(wme)

    @classmethod
    def remove_wme(cls, wme):
        """
        :type wme: WME
        """
        for am in wme.amems:
            am.items.remove(wme)
        for t in wme.tokens:
            Token.delete_token_and_descendents(t)
        for jr in wme.negative_join_result:
            jr.owner.join_results.remove(jr)
            if not jr.owner.join_results:
                for child in jr.owner.node.children:
                    child.left_activation(jr.owner, None)

    def build_or_share_alpha_memory(self, condition):
        """
        :type condition: Condition
        :rtype: AlphaMemory
        """
        path = []
        for f in FIELDS:
            v = getattr(condition, f)
            if not isinstance(v, Var):
                path.append((f, v))
        am = ConstantTestNode.build_or_share_alpha_memory(self.alpha_root, path)
        for w in self.alpha_root.amem.items:
            if condition.test(w):
                am.activation(w)
        return am

    @classmethod
    def get_join_tests_from_condition(cls, c, earlier_conds):
        """
        :type c: Condition
        :type earlier_conds: list of Condition
        :rtype: list of TestAtJoinNode
        """
        result = []
        for v in c.vars:
            for idx, cond in enumerate(earlier_conds):
                v2 = cond.contain(v)
                if not v2 or not cond.positive:
                    continue
                t = TestAtJoinNode(v.field, idx, v2.field)
                result.append(t)
        return result

    @classmethod
    def build_or_share_join_node(cls, parent, amem, tests):
        """
        :type parent: BetaNode
        :type amem: AlphaMemory
        :type tests: list of TestAtJoinNode
        :rtype: JoinNode
        """
        for child in parent.children:
            if isinstance(child, JoinNode) and child.amem == amem and child.tests == tests:
                return child
        node = JoinNode([], parent, amem, tests)
        parent.children.append(node)
        amem.successors.append(node)
        return node

    @classmethod
    def build_or_share_negative_node(cls, parent, amem, tests):
        """
        :type parent: BetaNode
        :type amem: AlphaMemory
        :type tests: list of TestAtJoinNode
        :rtype: JoinNode
        """
        for child in parent.children:
            if isinstance(child, NegativeNode) and child.amem == amem and child.tests == tests:
                return child
        node = NegativeNode(parent=parent, amem=amem, tests=tests)
        parent.children.append(node)
        amem.successors.append(node)
        return node

    @classmethod
    def build_or_share_beta_memory(cls, parent):
        """
        :type parent: BetaNode
        :rtype: BetaMemory
        """
        for child in parent.children:
            if isinstance(child, BetaMemory):
                return child
        node = BetaMemory(None, parent)
        parent.children.append(node)
        cls.update_new_node_with_matches_from_above(node)
        return node

    def build_or_share_ncc_nodes(self, parent, c, earlier_conds):
        """
        :type earlier_conds: list of Condition
        :type c: NCCondition
        :type parent: BetaNode
        """
        bottom_of_subnetwork = self.build_or_share_network_for_conditions(parent, c.cond_list, earlier_conds)
        for child in parent.children:
            if isinstance(child, NCCNode) and child.partner.parent == bottom_of_subnetwork:
                return child
        ncc_node = NCCNode([], parent)
        ncc_partner = NCCPartnerNode([], bottom_of_subnetwork)
        parent.children.append(ncc_node)
        bottom_of_subnetwork.children.append(ncc_partner)
        ncc_node.partner = ncc_partner
        ncc_partner.ncc_node = ncc_node
        ncc_partner.number_of_conditions = c.number_of_conditions
        self.update_new_node_with_matches_from_above(ncc_node)
        self.update_new_node_with_matches_from_above(ncc_partner)
        return ncc_node

    def build_or_share_network_for_conditions(self, parent, conds, earlier_conds):
        """
        :type earlier_conds: list of Condition
        :type parent: BetaNode
        :type conds: list of Condition
        """
        current_node = parent
        conds_higher_up = earlier_conds
        for cond in conds:
            if isinstance(cond, Condition) and cond.positive:
                current_node = self.build_or_share_beta_memory(current_node)
                tests = self.get_join_tests_from_condition(cond, conds_higher_up)
                am = self.build_or_share_alpha_memory(cond)
                current_node = self.build_or_share_join_node(current_node, am, tests)
            elif isinstance(cond, Condition) and not cond.positive:
                tests = self.get_join_tests_from_condition(cond, conds_higher_up)
                am = self.build_or_share_alpha_memory(cond)
                current_node = self.build_or_share_negative_node(current_node, am, tests)
            elif isinstance(cond, NCCondition):
                current_node = self.build_or_share_ncc_nodes(current_node, cond, conds_higher_up)
            conds_higher_up.append(cond)
        return current_node

    @classmethod
    def update_new_node_with_matches_from_above(cls, new_node):
        """
        :type new_node: BetaNode
        """
        parent = new_node.parent
        if isinstance(parent, BetaMemory):
            for tok in parent.items:
                parent.left_activation(tok)
        elif isinstance(parent, JoinNode):
            saved_list_of_children = parent.children
            parent.children = [new_node]
            for item in parent.amem.items:
                parent.right_activation(item)
            parent.children = saved_list_of_children
        elif isinstance(parent, NegativeNode):
            for token in parent.items:
                if not token.join_results:
                    new_node.left_activation(token, None)
        elif isinstance(parent, NCCNode):
            for token in parent.items:
                if not token.ncc_results:
                    new_node.left_activation(token, None)

    @classmethod
    def delete_node_and_any_unused_ancestors(cls, node):
        """
        :type node: BetaNode
        """
        if isinstance(node, JoinNode):
            node.amem.successors.remove(node)
        else:
            for item in node.items:
                Token.delete_token_and_descendents(item)
        node.parent.children.remove(node)
        if not node.parent.children:
            cls.delete_node_and_any_unused_ancestors(node.parent)
