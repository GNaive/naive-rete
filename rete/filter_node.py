import copy
from rete.common import BetaNode


class FilterNode(BetaNode):

    kind = 'filter-node'

    def __init__(self, children, parent, tmpl):
        """
        :type children:
        :type parent: BetaNode
        :type bind: str
        """
        super(FilterNode, self).__init__(children=children, parent=parent)
        self.tmpl = tmpl

    def left_activation(self, token, wme, binding=None):
        """
        :type binding: dict
        :type wme: WME
        :type token: Token
        """
        code = self.tmpl
        all_binding = token.all_binding()
        all_binding.update(binding)
        for k in all_binding:
            code = code.replace(k, str(all_binding[k]))
        result = eval(code)
        if bool(result):
            for child in self.children:
                child.left_activation(token, wme, binding)
