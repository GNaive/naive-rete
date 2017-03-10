from rete.common import BetaNode, Token


class BetaMemory(BetaNode):

    kind = 'beta-memory'

    def __init__(self, children=None, parent=None, items=None):
        """
        :type items: list of Token
        """
        super(BetaMemory, self).__init__(children=children, parent=parent)
        self.items = items if items else []
        self.children = children if children else []

    def left_activation(self, token, wme, binding=None):
        """
        :type binding: dict
        :type wme: WME
        :type token: Token
        """
        new_token = Token(token, wme, node=self, binding=binding)
        self.items.append(new_token)
        for child in self.children:
            child.left_activation(new_token)
