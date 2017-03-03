# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
from rete import Rule, Has, Neg, Filter, Bind, Ncc


def parse_xml(s):
    root = ET.fromstring(s)
    result = []
    for production in root:
        lhs = Rule()
        lhs.extend(parsing(production[0]))
        rhs = production[1].attrib
        result.append((lhs, rhs))
    return result


def parsing(root):
    out = []
    for cond in root:
        if cond.tag == 'has':
            out.append(Has(**cond.attrib))
        elif cond.tag == 'neg':
            out.append(Neg(**cond.attrib))
        elif cond.tag == 'filter':
            out.append(Filter(cond.text))
        elif cond.tag == 'bind':
            to = cond.attrib.get('to')
            out.append(Bind(cond.text, to))
        elif cond.tag == 'ncc':
            n = Ncc()
            n.extend(parsing(cond))
            out.append(n)
    return out
