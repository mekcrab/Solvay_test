'''
Module contains grammar definitions for state/transition attributes in plantUML state diagrams.

These definitions are directly utilized by the AttributeParser to generate the correct AttributeType
'''

import pyparsing as pp

__author__ = 'erik'

# ====== Utility Functions ============

def keyword_list(list_in):
    '''Generates a list of pyparsing.CaselessKeyword instances from a list of strings'''
    return pp.Or(map(pp.CaselessKeyword, list_in))


# ========Grammar definitions============

# ***Comparison Operators***
EQUALS = keyword_list(['=', 'equal', 'equals', 'is', 'to'])
GT = keyword_list(['>', 'greater than', 'more than', 'is greater than', 'not less than'])
LT = keyword_list(['<', 'less than', 'is less than', 'not more than'])
GTE = pp.Literal('>=')
LTE = pp.Literal('<=')
NOTEQUAL = keyword_list(['<>', 'not equal', '!='])
compare = GT ^ LT ^ GTE ^ LTE ^ EQUALS ^ NOTEQUAL
ASSIGN = pp.Literal(':=')
operator = (compare ^ ASSIGN).setResultsName('operator')

# ***Logicals***
OR = pp.CaselessKeyword('OR')
AND = pp.CaselessKeyword('AND')
NOT = pp.CaselessKeyword('NOT')
logical = (AND ^ OR ^ NOT)

# ***Primitive data types for comparisons***
NUMBER = pp.Combine(pp.Word(pp.nums) + pp.Optional(pp.Literal('.') + pp.Word(pp.nums)))
STRING = pp.dblQuotedString
TRUE = pp.CaselessKeyword('TRUE')
FALSE = pp.CaselessKeyword('FALSE')
BOOL = (TRUE ^ FALSE)


# Engineering units
eng_units = keyword_list(['lbs', 'pounds', 'percent', '\%', 'psig', 'scfm', 'F', 'C'])

# Time units
time_units = keyword_list(['minutes', 'mintue', 'min', 'm',
                           'hour', 'hours', 'h',
                           'sec', 's', 'second', 'seconds',
                           'days', 'd'])


# OPC path, forward slash delimited
opc_path = pp.Group(
    pp.delimitedList(pp.Word(pp.alphanums+'-_$'), delim='/', combine=True).setResultsName('path') + \
    pp.Optional(pp.Literal('.') + keyword_list(['CV', 'ST', 'CVI', 'CST'])).setResultsName('datatype'))

# OPC tag
tick = pp.Literal('\'')
tag = pp.Combine(pp.Suppress(tick + pp.Optional('/')) + (pp.Word(pp.alphanums+'-_$') ^ opc_path) + pp.Suppress(tick)). \
    setResultsName('tag')

# Word at the begining of the raw string
modes = keyword_list(['LO', 'MAN', 'IMAN', 'AUTO', 'CAS', 'ROUT', 'RCAS'])

# Map of keywords which define Attribute execution types. Keywords are based on execution types.
# Grammar is restricted such that keywords should be the first word of the raw attribute string (EFK as of 3/1/2016).
#   This restriction may be lifted in future versions...

# ===write keywords===
write_keyword = keyword_list(['set', 'write', 'force']).setResultsName('write')
# some shorthand write commands
open_vlv = keyword_list(['open', 'start', 'turn on']).setResultsName('open')   # data type based on control module tag
close_vlv = keyword_list(['close', 'stop', 'turn off']).setResultsName('close')
ramp = pp.CaselessKeyword('ramp').setResultsName('ramp')

# ===read keywords===
read_keyword = keyword_list(['read', 'get', 'check', 'verify']).setResultsName('read')
wait_keyword = keyword_list(['wait', 'wait until']).setResultsName('wait')
wait_time = (wait_keyword + NUMBER.setResultsName('value') + time_units.setResultsName('units')).setResultsName('wait_time')

# ===OAR prompt keywords===
prompt = (keyword_list(['prompt', 'oar', 'ack', 'ack', 'ask', 'message']) +
          pp.Optional(pp.Suppress('operator'))) + pp.dblQuotedString
prompt = prompt.setResultsName('prompt')

# ===Report parameters for batch===
report = keyword_list(['record', ]).setResultsName('report')

# ======catch-all to allow creation/execution of diagrams with direct OPC commands======
# will be the most structured of all attribute strings
# write OPC path, value
set_opc = (pp.CaselessKeyword('Write OPC') +
           pp.Group(pp.OneOrMore(tag ^ opc_path)).setResultsName('paths')). \
    setResultsName('write_opc')
# read OPC path
get_opc = (pp.CaselessKeyword('Read OPC') +
           pp.Group(pp.OneOrMore(tag ^ opc_path)).setResultsName('paths')). \
    setResultsName('read_opc')

# action words as the first part of an argument, followed by one or more expressions
action_word = pp.Or(write_keyword ^ open_vlv ^ close_vlv ^ read_keyword ^ wait_keyword)  # matches longest string in argument
# action phrases do not require expressions to correctly parse
action_phrase = prompt ^ wait_time ^ get_opc ^ set_opc

# ===========Expressions=================
value = pp.Combine((tag ^ NUMBER ^ BOOL ^ modes) + pp.Optional(pp.Suppress(eng_units))). \
    setResultsName('value', listAllMatches=True)

condition = (tag + (operator ^ logical) + value ).setResultsName('condition')

command = (tag + pp.Optional(operator) + value +
           pp.Optional((pp.Suppress(keyword_list(['in', 'at', ',', 'to'])) + value))
           ).setResultsName('command')

expression = condition ^ command

# ==========Compound Expressions=========
compound_exp = (expression + pp.Optional(pp.OneOrMore(logical + expression))).setResultsName('expression', listAllMatches=True)

# =========keyword-based actions=========
action = (action_word.setResultsName('action_word') + (compound_exp ^ tag)) ^ action_phrase

