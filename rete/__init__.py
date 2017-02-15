# -*- coding: utf-8 -*-


FIELDS = ['identifier', 'attribute', 'value']


class ConstantTestNode:

    def __init__(self, field_to_test, field_must_equal=None, alpha_memory=None, children=None):
        """
        :type field_to_test: str
        :type children: list of ConstantTestNode
        :type alpha_memory: AlphaMemory
        """
        self.field_to_test = field_to_test
        self.field_must_equal = field_must_equal
        self.amem = alpha_memory
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
        next_node = None
        for child in node.children:
            if child.field_to_test == f and child.field_must_equal == v:
                next_node = child
                break
        if not next_node:
            next_node = ConstantTestNode(f, v, children=[])
            node.children.append(next_node)
        return cls.build_or_share_alpha_memory(next_node, path)


class WME:

    def __init__(self, identifier, attribute, value):
        self.identifier = identifier
        self.attribute = attribute
        self.value = value

    def __repr__(self):
        return "<WME (%s ^%s %s)>" % (self.identifier, self.attribute, self.value)


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
        for child in self.successors:
            child.right_activation(wme)


class Token:

    def __init__(self, parent, wme):
        """
        :type wme: WME
        :type parent: Token
        """
        if not isinstance(parent, Token):
            self.wmes = [wme]
        else:
            self.wmes = [w for w in parent.wmes] + [wme]

    def __repr__(self):
        return "<Token %s>" % self.wmes

    def __eq__(self, other):
        return self.wmes == other.wmes


class BetaNode(object):

    def __init__(self, children=None, parent=None):
        self.children = children if children else []
        self.parent = parent


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
        :type token: Token
        """
        if not token:
            new_token = Token(None, wme)
        else:
            new_token = Token(token, wme)
        self.items.append(new_token)
        for child in self.children:
            child.left_activation(new_token)


class JoinNode(BetaNode):

    kind = 'join-node'

    def __init__(self, children, parent, alpha_memory, tests):
        """
        :type children:
        :type parent: BetaMemory
        :type alpha_memory: AlphaMemory
        :type tests: list of TestAtJoinNode
        """
        super(JoinNode, self).__init__(children=children, parent=parent)
        self.alpha_memory = alpha_memory
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
        for wme in self.alpha_memory.items:
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
        return "<TestAtJoinNode WME.%s=Condition%s.%s?>" % (self.field_of_arg1, self.condition_number_of_arg2, self.field_of_arg2)

    def __eq__(self, other):
        return isinstance(other, TestAtJoinNode) and \
            self.field_of_arg1 == other.field_of_arg1 and \
            self.field_of_arg2 == other.field_of_arg2 and \
            self.condition_number_of_arg2 == other.condition_number_of_arg2


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

    def __init__(self, identifier, attribute, value):
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


class Network:

    def __init__(self):
        self.alpha_root = ConstantTestNode('no-test')
        self.beta_root = BetaMemory()

    def add_production(self, lhs):
        """
        :type lhs: list of Condition
        """
        earlier_conditions = []
        current_node = self.beta_root
        for c in lhs:
            # get the join node
            tests = self.get_join_tests_from_condition(c, earlier_conditions)
            am = self.build_or_share_alpha_memory(c)
            current_node = self.build_or_share_join_node(current_node, am, tests)

            # get the beta memory node
            current_node = self.build_or_share_beta_memory(current_node)
            earlier_conditions.append(c)

    def add_wme(self, wme):
        self.alpha_root.activation(wme)

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
        return ConstantTestNode.build_or_share_alpha_memory(self.alpha_root, path)

    @classmethod
    def get_join_tests_from_condition(cls, c, earlier_conds):
        """
        :type c: Condition
        :type earlier_conds: list of Condition
        :rtype: list of TestAtJoinNode
        """
        tests = []
        for v in c.vars:
            for idx, cond in enumerate(earlier_conds):
                v2 = cond.contain(v)
                if not v2:
                    continue
                t = TestAtJoinNode(v.field, idx, v2.field)
                tests.append(t)
        return tests

    @classmethod
    def build_or_share_join_node(cls, parent, alpha_memory, tests):
        """
        :type parent: BetaNode
        :type alpha_memory: AlphaMemory
        :type tests: list of TestAtJoinNode
        :rtype: JoinNode
        """
        for child in parent.children:
            if isinstance(child, JoinNode) and child.alpha_memory == alpha_memory and child.tests == tests:
                return child
        node = JoinNode([], parent, alpha_memory, tests)
        parent.children.append(node)
        alpha_memory.successors.append(node)
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
        return node
