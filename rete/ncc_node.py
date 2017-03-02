from rete.common import Token, BetaNode


class NccNode(BetaNode):

    def __init__(self, children=None, parent=None, items=None, partner=None):
        """
        :type partner: NccPartnerNode
        :type items: list of rete.Token
        """
        super(NccNode, self).__init__(children=children, parent=parent)
        self.items = items if items else []
        self.partner = partner

    def left_activation(self, t, w, binding=None):
        """
        :type w: rete.WME
        :type t: rete.Token
        :type binding: dict
        """
        new_token = Token(t, w, self, binding)
        self.items.append(new_token)
        for result in self.partner.new_result_buffer:
            self.partner.new_result_buffer.remove(result)
            new_token.ncc_results.append(result)
            result.owner = new_token
        if not new_token.ncc_results:
            for child in self.children:
                child.left_activation(new_token, None)


class NccPartnerNode(BetaNode):

    def __init__(self, children=None, parent=None, ncc_node=None,
                 number_of_conditions=0, new_result_buffer=None):
        """
        :type new_result_buffer: list of rete.Token
        :type ncc_node: NccNode
        """
        super(NccPartnerNode, self).__init__(children=children, parent=parent)
        self.ncc_node = ncc_node
        self.number_of_conditions = number_of_conditions
        self.new_result_buffer = new_result_buffer if new_result_buffer else []

    def left_activation(self, t, w, binding=None):
        """
        :type w: rete.WME
        :type t: rete.Token
        :type binding: dict
        """
        new_result = Token(t, w, self, binding)
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
