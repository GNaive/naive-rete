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
        return "(%s ^%s %s)" % (self.identifier, self.attribute, self.value)

    def __eq__(self, other):
        """
        :type other: WME
        """
        if not isinstance(other, WME):
            return False
        return self.identifier == other.identifier and \
            self.attribute == other.attribute and \
            self.value == other.value


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
        if wme in self.items:
            return
        self.items.append(wme)
        wme.amems.append(self)
        for child in reversed(self.successors):
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
        self.ncc_results = []
        self.owner = None  # NCC

        if self.wme:
            self.wme.tokens.append(self)
        if self.parent:
            self.parent.children.append(self)

    def __repr__(self):
        return "<Token %s>" % self.wmes

    def __eq__(self, other):
        return isinstance(other, Token) and \
               self.parent == other.parent and self.wme == other.wme

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
        if not isinstance(token.node, NCCPartnerNode):
            token.node.items.remove(token)
        if token.wme:
            token.wme.tokens.remove(token)
        if token.parent:
            token.parent.children.remove(token)
        if isinstance(token.node, NegativeNode):
            for jr in token.join_results:
                jr.wme.negative_join_results.remove(jr)
        elif isinstance(token.node, NCCNode):
            for result_tok in token.ncc_results:
                result_tok.wme.tokens.remove(result_tok)
                result_tok.parent.children.remove(result_tok)
        elif isinstance(token.node, NCCPartnerNode):
            token.owner.ncc_results.remove(token)
            if not token.owner.ncc_results:
                for child in token.node.ncc_node.children:
                    child.left_activation(token.owner, None)


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


class NCCNode(BetaNode):

    def __init__(self, children=None, parent=None, items=None, partner=None):
        """
        :type partner: NCCPartnerNode
        :type items: list of Token
        """
        super(NCCNode, self).__init__(children=children, parent=parent)
        self.items = items if items else []
        self.partner = partner

    def left_activation(self, t, w):
        """
        :type w: WME
        :type t: Token
        """
        new_token = Token(t, w, self)
        self.items.append(new_token)
        for result in self.partner.new_result_buffer:
            self.partner.new_result_buffer.remove(result)
            new_token.ncc_results.append(result)
            result.owner = new_token
        if not new_token.ncc_results:
            for child in self.children:
                child.left_activation(new_token, None)


class NCCPartnerNode(BetaNode):

    def __init__(self, children=None, parent=None, ncc_node=None,
                 number_of_conditions=0, new_result_buffer=None):
        """
        :type new_result_buffer: list of Token
        :type ncc_node: NCCNode
        """
        super(NCCPartnerNode, self).__init__(children=children, parent=parent)
        self.ncc_node = ncc_node
        self.number_of_conditions = number_of_conditions
        self.new_result_buffer = new_result_buffer if new_result_buffer else []

    def left_activation(self, t, w):
        """
        :type w: WME
        :type t: Token
        """
        new_result = Token(t, w, self)
        owners_t = t
        owners_w = w
        for i in range(self.number_of_conditions):
            owners_w = owners_t.wme
            owners_t = owners_t.parent
        for token in self.ncc_node.items:
            if token.parent == owners_t and token.wme == owners_w:
                token.ncc_results.append(new_result)
                new_result.owner = token
                Token.delete_token_and_descendents(token)
        self.new_result_buffer.append(new_result)


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


class NCCondition:

    def __init__(self, cond_list):
        """
        :type cond_list: list of Condition
        """
        self.cond_list = cond_list

    @property
    def number_of_conditions(self):
        return len(filter(lambda x: isinstance(x, Condition), self.cond_list))
