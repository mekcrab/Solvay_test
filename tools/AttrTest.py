from lxml.html import _element_name

import StateModel
import Attributes.AttributeTypes as AttributeTypes
import random

def make_attribute():
    '''makes a random constant integer from 0-10'''
    return AttributeTypes.Constant(random.randint(0,10))

def make_state_diagram(s=1, t=0):
    '''makes a single-path diagram of random states and transitions'''
    new_diagram = StateModel.StateDiagram(id='test diagram')

    for snum in range(s):
        sname = 'state'+str(snum)
        new_diagram.add_state(sname)

        [new_diagram.add_state_attr(sname, make_attribute()) for x in range(random.randint(1,5))]

    for tnum in range(t):
        print "Transitions not yet implemented"

    return new_diagram


if __name__ == "__main__":

    d = make_state_diagram()
    s = d.top_level[0]
    a = s.attrs[0]

    print d.state_names





