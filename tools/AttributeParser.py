'''
Module contains class definitions to parse attribute strings into classes defined in AttributeTypes.

Parser is context sensitive based on a set of controlled keywords, tags, the class of the Control Module in DeltaV
(or component function blocks), and various modifiers. The goal is to have a flexible, natural language that
deterministically defined a single AttributeType.


'''


from Utilities.Logger import LogTools
dlog = LogTools('AttributeParsing.log', 'AttributeParser')
dlog.rootlog.warning('Module initialized')

import kessel

# define grammar





class AttrParser(object):
    '''Essentially an AttributeTypes instance factory when fed attribute strings

    Attribute grammar is as follows:


    Attribute keywords:


    '''

    def __init__(self):
        '''Constructor'''


    def parse(self, attribute_string):
        pass

        # search for tags in raw string, resolve tag type from DeltaV

        # search for keywords/operators to determine execution type

        # find tag modifiers and optional arguments




