'''
Module contains class definitions to parse attribute strings into classes defined in AttributeTypes.

Parser is context sensitive based on a set of controlled keywords, tags, the class of the Control Module in DeltaV
(or component function blocks), and various modifiers. The goal is to have a flexible, natural language that
deterministically defined a single AttributeType.

============Grammar definition:=================
tag - single quote enclosed for DeltaV tag names, can also be aliased based on embedded modules or unit aliases
#TODO: fill in keywords and other aspects of the grammar definition

============Example attribute raw strings:============

Open 'CV-2394'
Set 'PIC-1899' to 100 in AUTO

Open 'N2_VALVE' in Auto with a setpoint of 2 psig
Open 'N2_VALVE' in auto SP 2psig

Verify 'PIC-3851' > 125 F
Check 'FIC-1795' is in ROUT

Wait until 'LI-398' is less than 100 lbs

ACK operator "Sodium Borohydride Charge is Completed

Wait 30 minutes

***Future extensions***
Heat/Cool mode in auto at (Reaction Temp +2F)
Wait for reactor temperature > Reaction Temp degF
Wait for Hydrolysis Hold Time minutes
Slowly ramp open the vent vale to ATM
'''


from tools.Utilities.Logger import LogTools
dlog = LogTools('AttributeParsing.log', 'AttributeParser')
dlog.rootlog.warning('Module initialized')

import pyparsing as pp

def keyword_list(list_in):
    '''Generates a list of pyparsing.CaselessKeyword instances from a list of strings'''
    return map(pp.CaselessKeyword, list_in)

# ========Grammar definitions============

# ***Comparison Operators***
EQUALS = pp.pp.Literal('=')
NEQUALS = pp.pp.Literal('!=')
GT = pp.Literal('>')
LT = pp.Literal('<')
GTE = pp.Literal('>=')
LTE = pp.Literal('<=')
NOTEQUAL = pp.Literal('<>')
compare = GT ^ LT ^ GTE ^ LTE ^ EQUALS ^ NOTEQUAL ^ NEQUALS

# ***Logicals***
OR = pp.CaselessKeyword('OR')
AND = pp.CaselessKeyword('AND')
NOT = pp.CaselessKeyword('NOT')
logical = (AND ^ OR ^ NOT)

# ***Primitive data types for comparisons***
NUMBER = pp.Word(pp.nums + '.').setResultsName('number')
STRING = pp.dblQuotedString.setResultsName('string')
TRUE = pp.CaselessKeyword('TRUE')
FALSE = pp.CaselessKeyword('FALSE')
BOOL = (TRUE ^ FALSE).setResultsName('boolean')

# OPC path, forward slash delimited
opc_path = pp.delimitedList(pp.alphanumbs, delim='/')
# DeltaV tag
tag = pp.sglQuotedString(pp.Optional(pp.Literal('/')) +
                         pp.Word(pp.alphanums ^ '-_$') +
                         pp.Optional(opc_path))

# Word at the begining of the raw string
execution_type = pp.StringStart(pp.Word(pp.alphas))

modes = pp.Or( keyword_list(['LO', 'MAN', 'IMAN', 'AUTO', 'CAS', 'ROUT', 'RCAS']))

# Map of keywords which define Attribute execution types. Keywords are based on execution types.
# Grammar is restricted such that keywords should be the first word of the raw attribute string (EFK as of 3/1/2016).
#   This restriction may be lifted in future versions...

# ===write keywords===
write_keyword = pp.Or( keyword_list(['set', 'write', 'force']) )
# some shorthand write commands
open_vlv = pp.CaselessKeyword('open')   # data type based on control module tag
close_vlv = pp.CaselessKeyword('close')

# ===read keywords===
read_keyword = pp.Or( keyword_list(['read', 'get', 'check', 'verify']))


# ===OAR prompt keywords===
prompt = pp.Or( keyword_list(['prompt', 'oar', 'ack', 'ask']))


# ===catch-all to allow creation/execution of diagrams with direct OPC commands===
# will be the most structured of all attribute strings
# write OPC path, value
set_opc = pp.CaselessKeyword('Write OPC') + tag + ',' + pp.Or([pp.Word(pp.nums), pp.Word(pp.alphas)])
# read OPC path
get_opc = pp.CaselessKeyword('Read OPC') + tag          # read from OPC path


class AttributeParser(object):
    '''
    Essentially an AttributeTypes instance factory when fed attribute strings
    '''

    def __init__(self):
        '''Constructor'''
        pass

    def parse(self, attribute_string):
        pass

        # Check for keyword in the first position

        # If no keyword, determine execution type by context, below:
        # search for tags in raw string, resolve tag type from DeltaV

        # search for keywords/operators to determine execution type

        # find tag modifiers and optional arguments

    def create_attribute_instance(self):
        '''Creates a new attribute instance based on text parsing results'''
        pass

    def print_keywords(self):
        pass



