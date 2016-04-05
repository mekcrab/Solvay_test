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

def normalize(normal_value):
    '''returns function to normalize output of keyword lists'''
    return lambda s,l,t,n=normal_value: t.__setitem__(0,n)

# ========Grammar definitions============

# ***Comparison Operators***
EQUALS = keyword_list(['=', 'equal', 'equals', 'is', 'to']).setParseAction(normalize('='))
GT = keyword_list(['>', 'greater than', 'more than', 'is greater than', 'not less than']).setParseAction(normalize('>'))
LT = keyword_list(['<', 'less than', 'is less than', 'not more than']).setParseAction(normalize('<'))
GTE = pp.Literal('>=')
LTE = pp.Literal('<=')
NOTEQUAL = keyword_list(['<>', 'not equal', '!=']).setParseAction(normalize('!='))
compare = (GT ^ LT ^ GTE ^ LTE ^ EQUALS ^ NOTEQUAL).setResultsName('compare')
ASSIGN = pp.Literal(':=')
operator = (compare ^ ASSIGN).setResultsName('operator')

# ***Logicals***
OR = pp.CaselessKeyword('OR')
AND = pp.CaselessKeyword('AND')
NOT = pp.CaselessKeyword('NOT')
logical = (AND ^ OR ^ NOT)

# ***Primitive data types for comparisons***
NUMBER = pp.Regex(r'\d+(\.\d*)?')
STRING = pp.dblQuotedString
TRUE = pp.CaselessKeyword('TRUE').setParseAction(normalize(1))
FALSE = pp.CaselessKeyword('FALSE').setParseAction(normalize(0))
BOOL = (TRUE ^ FALSE)


# Engineering units
eng_units = keyword_list(['lbs', 'pounds', 'percent', '\%', 'psig', 'scfm', 'F', 'C', '%/second'])

# Time units
time_units = keyword_list(['minutes', 'mintue', 'min', 'm',
                           'hour', 'hours', 'h',
                           'sec', 's', 'second', 'seconds',
                           'days', 'd'])


# OPC path, forward slash delimited
opc_path = (pp.delimitedList(pp.Word(pp.alphanums+'-_$'), delim='/', combine=True).setResultsName('path') +
    pp.Optional(pp.Literal('.') + keyword_list(['CV', 'ST', 'CVI', 'CST'])).setResultsName('datatype'))

# OPC tag
tick = pp.Literal('\'')
tag = (pp.Suppress(tick + pp.Optional('/')) +
            (pp.Word(pp.alphanums+'-_$').setResultsName('tag') ^ opc_path) +
            pp.Suppress(tick))

# Mode keywords
LO = keyword_list(['LO', 'local_override', 'interlocked']).setParseAction(normalize('LO'))
MAN = keyword_list(['MAN', 'manual']).setParseAction(normalize('MAN'))
IMAN = keyword_list(['init manual', 'initialize manual', 'IMAN']).setParseAction(normalize('IMAN'))
AUTO = keyword_list(['AUTO', 'Automatic']).setParseAction(normalize('AUTO'))
CAS = keyword_list(['CAS', 'cascade']).setParseAction(normalize('CAS'))
RCAS = keyword_list(['RCAS', 'remote cascade', 'remote auto']).setParseAction(normalize('RCAS'))
ROUT = keyword_list(['ROUT', 'remote output', 'remote out', 'remote manual']).setParseAction(normalize('ROUT'))
modes = (LO ^ MAN ^ IMAN ^ AUTO ^ CAS ^ RCAS ^ ROUT)

# Map of action keywords which define Attribute execution types. Keywords are based on execution types.
# Grammar is restricted such that keywords should be the first word of the raw attribute string (EFK as of 3/1/2016).
#   This restriction may be lifted in future versions...

# ===write keywords===
write_keyword = keyword_list(['set', 'write', 'force']).setParseAction(normalize('write'))
# some shorthand write commands
open_vlv = keyword_list(['open', 'opened']).setParseAction(normalize('open'))   # check data type based on control module tag
close_vlv = keyword_list(['close', 'closed', 'shut']).setParseAction(normalize('close'))
start_mtr = keyword_list(['on', 'turn on', 'start', 'started', 'run', 'running']).setParseAction(normalize('start'))
stop_mtr = keyword_list(['off', 'stop', 'shutdown', 'stopped']).setParseAction(normalize('stop'))
ramp = pp.CaselessKeyword('ramp').setParseAction(normalize('ramp'))
ilk_trip = keyword_list(['trip', 'tripped', 'interlock trip']).setParseAction(normalize('trip'))
ilk_reset = keyword_list(['reset', 'interlock reset']).setParseAction(normalize('reset'))

# ===read keywords===
read_keyword = keyword_list(['read', 'get', 'check', 'check that', 'check if', 'verify', 'if'])\
    .setParseAction(normalize('read'))
wait_keyword = keyword_list(['wait', 'wait until', 'wait for', 'delay']).setParseAction(normalize('wait'))
wait_time = (wait_keyword + NUMBER.setResultsName('value') + time_units.setResultsName('units')).setResultsName('wait_time')


# ===OAR prompt keywords===
prompt = (keyword_list(['prompt', 'oar', 'ack', 'ack', 'ask', 'message']) +
          pp.Optional(pp.Suppress(pp.OneOrMore(keyword_list(['operator', 'message', ':', 'response', '='])))) +
          (STRING.setResultsName('message') ^ keyword_list(['VALUE', 'YES', 'NO', 'INFO']).setResultsName('target')))
prompt = prompt.setParseAction(normalize('prompt'))

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

# ============= Action Keywords and Action Phrases======
# action words as the first part of an argument, followed by one or more expressions
action_word = pp.Or(write_keyword ^ read_keyword ^ open_vlv ^ close_vlv ^ start_mtr ^ stop_mtr ^ wait_keyword)  # NOTE:: pp.Or matches longest string in argument - could introduce bug for overlapping lists
# action phrases do not require expressions to correctly parse
action_phrase = prompt ^ wait_time ^ get_opc ^ set_opc

# ===========Expressions - each type below returns a ParseResult=================
value = ((tag ^ NUMBER ^ BOOL ^ modes ^ STRING ^ open_vlv ^ close_vlv ^ start_mtr ^ stop_mtr ^ ilk_trip ^ ilk_reset) +
         pp.Suppress(pp.Optional(eng_units))).setResultsName('value')

condition = (pp.Group(tag).setResultsName('lhs') + compare + pp.Group(value).setResultsName('rhs')). \
            setResultsName('condition')

command = (tag + pp.Optional(EQUALS ^ ASSIGN) + pp.Optional(keyword_list(['in', 'at', ',', 'to']).suppress()) + value +
            pp.Optional(keyword_list(['in', 'at', ',', 'to']).suppress() + value)).\
            setResultsName('command')

# ==========Compound Expressions=========
compound_exp = ((condition ^ command) + pp.ZeroOrMore(logical + (condition ^ command))).setResultsName('expression', listAllMatches=True)

# =========keyword-based actions=========
action = (action_word.setResultsName('action_word') +
         ((compound_exp ^ tag) + pp.Optional(value))) ^ \
                action_phrase.setResultsName('action_phrase')

