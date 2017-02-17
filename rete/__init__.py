# -*- coding: utf-8 -*-


FIELDS = ['identifier', 'attribute', 'value']


class ConstantTestNode:

    def __init__(self, field_to_test, field_must_equal=None, amem=None, children=None):
        """
        :type field_to_test: str
        :type children: list of ConstantTestNode
        :type amem: AlphaMemory
        """
        self.field_to_test = field_to_test
        self.field_must_equal = field_must_equal
        self.amem = amem
        self.children = children if children else list()

    def __repr__(self):
        return "<ConstantTestNode %s=%s?>" % (self.field_to_test, self.field_must_equal)

    def activation(self, wme):
        """
        :type wme: WME
        """
        if self.field_to_test != 'no-test':
            v = getattr(wme, self.field_to_test)
            if v != self.field_must_equal:
                return False
        if self.amem:
            self.amem.activation(wme)
        for child in self.children:
            child.activation(wme)

    @classmethod
    def build_or_share_alpha_memory(cls, node, path=[]):
        """
        :type node: ConstantTestNode
        :type path: [(field, value)...]
        :rtype: AlphaMemory
        """
        if not len(path):
            if node.amem:
                return node.amem
            else:
                am = AlphaMemory()
                node.amem = am
                return am
        f, v = path.pop(0)
        assert f in FIELDS, "`%s` not in %s" % (f, FIELDS)
        next_node = cls.build_or_share_constant_test_node(node, f, v)
        return cls.build_or_share_alpha_memory(next_node, path)

    @classmethod
    def build_or_share_constant_test_node(cls, parent, field, symbol):
        """
        :rtype: ConstantTestNode
        :type symbol: str
        :type field: str
        :type parent: ConstantTestNode
        """
        for child in parent.children:
            if child.field_to_test == field and child.field_must_equal == symbol:
                return child
        new_node = ConstantTestNode(field, symbol, children=[])
        parent.children.append(new_node)
        return new_node


class WME:

    def __init__(self, identifier, attribute, value):
        self.identifier = identifier
        self.attribute = attribute
        self.value = value
        self.amems = []  # the ones containing this WME
        self.tokens = []  # the ones containing this WME
        self.negative_join_result = []

    def __repr__(self):
        return "<WME(%s ^%s %s)>" % (self.identifier, self.attribute, self.value)


class AlphaMemory:

    def __init__(self, items=None, successors=None):
        """
        :type successors: list of BetaNode
        :type items: list of WME
        """
        self.items = items if items else []
        self.successors = successors if successors else []

    def activation(self, wme):
        """
        :type wme: WME
        """
        self.items.append(wme)
        wme.amems.append(self)
        for child in self.successors:
            child.right_activation(wme)


class Token:

    def __init__(self, parent, wme, node=None):
        """
        :type wme: WME
        :type parent: Token
        """
        self.parent = parent
        self.wme = wme
        self.node = node  # points to memory this token is in
        self.children = []  # the ones with parent = this token
        self.join_results = []  # used only on tokens in negative nodes

        if self.wme:
            self.wme.tokens.append(self)
        if self.parent:
            self.parent.children.append(self)

    def __repr__(self):
        return "<Token %s>" % self.wmes

    def __eq__(self, other):
        return self.wme == other.wme and self.parent == other.parent

    @property
    def wmes(self):
        ret = [self.wme]
        t = self
        while t.parent:
            t = t.parent
            ret.insert(0, t.wme)
        return ret

    @classmethod
    def delete_token_and_descendents(cls, token):
        """
        :type token: Token
        """
        for child in token.children:
            cls.delete_token_and_descendents(child)
        token.node.items.remove(token)
        if token.wme:
            token.wme.tokens.remove(token)
        if token.parent:
            token.parent.children.remove(token)
        if isinstance(token.node, NegativeNode):
            for jr in token.join_results:
                jr.wme.negative_join_results.remove(jr)


class NegativeJoinResult:

    def __init__(self, owner, wme):
        """
        :type wme: WME
        :type owner: Token
        """
        self.owner = owner
        self.wme = wme


class BetaNode(object):

    def __init__(self, children=None, parent=None):
        self.children = children if children else []
        self.parent = parent

    def right_activation(self, wme):
        """
        :type wme: WME
        """
        pass


class BetaMemory(BetaNode):

    kind = 'beta-memory'

    def __init__(self, children=None, parent=None, items=None):
        """
        :type items: list of Token
        """
        super(BetaMemory, self).__init__(children=children, parent=parent)
        self.items = items if items else []
        self.children = children if children else []

    def left_activation(self, token, wme):
        """
        :type wme: WME
        :type token: Token
        """
        new_token = Token(token, wme, node=self)
        # avoiding duplicate tokens
        if new_token in self.items:
            if new_token.parent:
                new_token.parent.children.pop()
            new_token.wme.tokens.pop()
            return
        self.items.append(new_token)
        for child in self.children:
            child.left_activation(new_token)


class JoinNode(BetaNode):

    kind = 'join-node'

    def __init__(self, children, parent, amem, tests):
        """
        :type children:
        :type parent: BetaNode
        :type amem: AlphaMemory
        :type tests: list of TestAtJoinNode
        """
        super(JoinNode, self).__init__(children=children, parent=parent)
        self.amem = amem
        self.tests = tests

    def right_activation(self, wme):
        """
        :type wme: WME
        """
        # dummy join node
        if not self.tests:
            for child in self.children:
                child.left_activation(None, wme)

        for token in self.parent.items:
            if self.perform_join_test(token, wme):
                for child in self.children:
                    child.left_activation(token, wme)

    def left_activation(self, token):
        """
        :type token: Token
        """
        for wme in self.amem.items:
            if self.perform_join_test(token, wme):
                for child in self.children:
                    child.left_activation(token, wme)
            
    def perform_join_test(self, token, wme):
        """
        :type token: Token
        :type wme: WME
        """
        for this_test in self.tests:
            arg1 = getattr(wme, this_test.field_of_arg1)
            wme2 = token.wmes[this_test.condition_number_of_arg2]
            arg2 = getattr(wme2, this_test.field_of_arg2)
            if arg1 != arg2:
                return False
        return True


class TestAtJoinNode:

    def __init__(self, field_of_arg1, condition_number_of_arg2, field_of_arg2):
        self.field_of_arg1 = field_of_arg1
        self.condition_number_of_arg2 = condition_number_of_arg2
        self.field_of_arg2 = field_of_arg2

    def __repr__(self):
        return "<TestAtJoinNode WME.%s=Condition%s.%s?>" % (
            self.field_of_arg1, self.condition_number_of_arg2, self.field_of_arg2)

    def __eq__(self, other):
        return isinstance(other, TestAtJoinNode) and \
            self.field_of_arg1 == other.field_of_arg1 and \
            self.field_of_arg2 == other.field_of_arg2 and \
            self.condition_number_of_arg2 == other.condition_number_of_arg2


class NegativeNode(BetaNode):

    def __init__(self, children=None, parent=None, amem=None, tests=None):
        """
        :type amem: AlphaMemory
        """
        super(NegativeNode, self).__init__(children=children, parent=parent)
        self.items = []
        self.amem = amem
        self.tests = tests if tests else []

    def left_activation(self, token, wme):
        """
        :type wme: WME
        :type token: Token
        """
        new_token = Token(token, wme, self)
        self.items.append(new_token)
        for item in self.amem.items:
            if self.perform_join_test(new_token, item):
                jr = NegativeJoinResult(new_token, item)
                new_token.join_results.append(jr)
                item.negative_join_result.append(jr)
        if not new_token.join_results:
            for child in self.children:
                child.left_activation(new_token, None)

    def right_activation(self, wme):
        """
        :type wme: WME
        """
        for t in self.items:
            if self.perform_join_test(t, wme):
                if not t.join_results:
                    Token.delete_token_and_descendents(t)
                jr = NegativeJoinResult(t, wme)
                t.join_results.append(jr)
                wme.negative_join_result.append(jr)

    def perform_join_test(self, token, wme):
        """
        :type token: Token
        :type wme: WME
        """
        for this_test in self.tests:
            arg1 = getattr(wme, this_test.field_of_arg1)
            wme2 = token.wmes[this_test.condition_number_of_arg2]
            arg2 = getattr(wme2, this_test.field_of_arg2)
            if arg1 != arg2:
                return False
        return True


class Var:

    def __init__(self, symbol, field=None):
        self.symbol = symbol
        self.field = field

    def __eq__(self, other):
        if not isinstance(other, Var):
            return False
        if other.symbol != self.symbol:
            return False
        return True


class Condition:

    def __init__(self, identifier, attribute, value, positive=True):
        """
        (<x> ^self <y>)
        repr as:
        (Var('x'), 'self', Var('y'))

        :type value: Var or str
        :type attribute: Var or str
        :type identifier: Var or str
        """
        self.value = value
        self.attribute = attribute
        self.identifier = identifier
        self.positive = positive

        for f in FIELDS:
            v = getattr(self, f)
            if isinstance(v, Var):
                v.field = f

    @property
    def vars(self):
        ret = []
        for f in FIELDS:
            v = getattr(self, f)
            if isinstance(v, Var):
                ret.append(v)
        return ret

    def contain(self, v):
        """
        :type v: Var
        :rtype: Var
        """
        for _v in self.vars:
            if v == _v:
                return _v
        return None

    def test(self, w):
        """
        :type w: WME
        """
        for f in FIELDS:
            v = getattr(self, f)
            if isinstance(v, Var):
                continue
            if v != getattr(w, f):
                return False
        return True


class Network:

    def __init__(self):
        self.alpha_root = ConstantTestNode('no-test', amem=AlphaMemory())
        self.beta_root = BetaMemory()

    def add_production(self, lhs):
        """
        :type lhs: list of Condition
        """
        earlier_conditions = []
        current_node = self.beta_root
        for idx, c in enumerate(lhs):
            tests = self.get_join_tests_from_condition(c, earlier_conditions)
            am = self.build_or_share_alpha_memory(c)
            if c.positive:
                # get the join node
                current_node = self.build_or_share_join_node(current_node, am, tests)
                if len(lhs) > idx + 1 and lhs[idx+1].positive or len(lhs) == idx + 1:
                    # get the beta memory node
                    current_node = self.build_or_share_beta_memory(current_node)
            else:
                # get the negative node
                current_node = self.build_or_share_negative_node(current_node, am, tests)
            earlier_conditions.append(c)
        return current_node

    def remove_production(self, node):
        self.delete_node_and_any_unused_ancestors(node)

    def add_wme(self, wme):
        self.alpha_root.activation(wme)

    def remove_wme(self, wme):
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
                if not v2:
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
