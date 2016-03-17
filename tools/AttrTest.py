from lxml.html import _element_name

import StateModel
import Attributes.AttributeTypes as AttributeTypes
import random


def rten():
    '''returns randome number from 1-10'''
    return random.randint(0,10)


def ropr():
    '''makes a random operator'''
    return random.choice(['>', '<', '>=', '<=', '!='])


def make_attribute(val=None):
    '''makes a random constant attribute'''
    return AttributeTypes.Constant(rten())


def make_pass_condition():
    '''makes a transition that will pass'''
    lhs = rten() + 2
    opr = ropr()
    if '>' in opr:
        rhs = random.randint(lhs+1, 2*lhs)
    else:
        rhs = random.randint(0, lhs-1)

    return AttributeTypes.Compare(AttributeTypes.Constant(lhs), opr, AttributeTypes.Constant(rhs))


def make_fail_condition():
    '''makes a transition that will fail'''
    lhs = rten() + 2
    opr = ropr()
    if '>' in opr:
        rhs = random.rint(0, lhs-1)
    else:
        rhs = random.rint(lhs+1, 2*lhs)

    return AttributeTypes.Compare(AttributeTypes.Constant(lhs), opr, AttributeTypes.Constant(rhs))


def make_state_diagram(s=1):
    '''makes a single-path diagram of random states and transitions'''
    new_diagram = StateModel.StateDiagram(id='test diagram')

    for snum in range(s):
        sname = 'state'+str(snum)
        new_diagram.add_state(sname)

        [new_diagram.add_state_attr(sname, make_attribute()) for x in range(random.randint(1,5))]

        if snum > 0 and snum != s:  #add transition between states
            new_diagram.add_transition('state'+str(snum-1), sname, attributes=make_pass_condition())

    return new_diagram


if __name__ == "__main__":

    d = make_state_diagram(s=2)
    s = d.top_level[0]
    print d.state_names

    t = d.transitions[0]
    a = t.attrs[0]

    print a.execute()



