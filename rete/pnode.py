from rete.common import BetaNode, Token


class PNode(BetaNode):

    kind = 'p'

    def __init__(self, children=None, parent=None, items=None, **kwargs):
        """
        :type items: list of Token
        """
        super(PNode, self).__init__(children=children, parent=parent)
        self.items = items if items else []
        self.children = children if children else []
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def left_activation(self, token, wme, binding=None):
        """
        :type wme: WME
        :type token: Token
        :type binding: dict
        """
        new_token = Token(token, wme, node=self, binding=binding)
        self.items.append(new_token)

    def execute(self, *args, **kwargs):
        raise NotImplementedError
