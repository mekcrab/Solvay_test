'''
Python module for lexing plantUML state diagrams.
'''
__author__ = 'ekopache'

import re
from pygments.lexer import RegexLexer, bygroups, include
from pygments.token import Name, Text, Error, _TokenType

# token definitions

STATE = Name.Class  # state definition
SALIAS = Name.Variable # state alias
SATTR = Name.Attribute # state attribute
SNOTE = Name.Label # state notes

TSOURCE = Name.Variable # transition source
TDEST = Name.Entity # transition destination
TATTR = Name.Other # transition attribute

IGNORE = Text # stuff to ignore

class puml_state_lexer(RegexLexer):

    def embedded_state(lexer, match, ctx):
        '''function provides for recursive lexing of embedded states'''
        print '***********Embedded state found: ********'
        for i,t,v in lexer.get_tokens_unprocessed(match._text, stack=('state',)):
            yield i,t,v


    # regex mode flags
    flags = re.MULTILINE

    tokens = {
        'root': [
            (r'(?i)^(hide|show)?[\s]*footbox$', IGNORE),
            (r'(?i)^(left[\s]to[\s]right|top[\s]to[\s]bottom)[\s]+direction$', IGNORE),
            (r'^(?:state[\s]+)'\
                 # STATE as "SALIAS" |
                '(?:([\w\.]+)[\s]+as[\s]+["]([^"\n]+)["]|'\
                # "STATE" as SALIAS |
                '["]([^"\n]+)["][\s]+as[\s]+([\w\.]+)|'\
                # STATE | "STATE"
                '([\w\.]+)|["]([^"\n]+)["])'\
                # skip spaces <<IGNORE>> skip spaces
                '[\s]*(\<\<.*\>\>)?[\s]*'\
                    # ([["IGNORE"]|[IGNORE]])
                    '(\[\[(["][^"\n]+["]|[^{}\s\]\[]*)'\
                    # non-cap inner state defs {} - RECURSIVE REGEX
                    '(?:[\s]*\{([^{}]+)\})?'\
                    # non-cap  inner defs [[]] - more recursion
                    '(?:[\s]*([^\]\[]+))?\]\])?'\
                    # hash then words
                    '[\s]*(#\w+[-\\|/]?\w+)?[\s]*'\
                    # non-cap ((non-cap string elide or [text format])?
                    '(?:##(?:\[(dotted|dashed|bold)\])?'\
                        # words)
                        '(\w+)?)?'\
                    # non-cap state attribute
                    '[\s]*(?::[\s]*(.*))?$',
                                    bygroups(SALIAS, STATE,
                                             STATE,
                                             IGNORE,
                                             embedded_state,
                                             embedded_state,
                                             IGNORE,
                                             IGNORE, IGNORE, IGNORE,
                                             SATTR),),
            (# TSOURCE
             r'^(?:[\s]*)([\w\.]+|[\w\.]+\[H\]|\[\*\]|\[H\]|(?:==+)(?:[\w\.]+)(?:==+))'\
             # <<IGNORE>>
             '[\s]*(\<\<.*\>\>)?[\s]*'\
             # IGNORE, IGNORE, IGNORE (transition start -+)
             '(#\w+)?[\s]*(x)?(-+)'\
             # IGNORE [# formatting crap ]
             '(?:\[('\
                '(?:#\w+|dotted|dashed|bold|hidden)'\
                '(?:,#\w+|,dotted|,dashed|,bold|,hidden)*)\])?'\
             #IGNORE (arrow direction)
             '(left|right|up|down|le?|ri?|up?|do?)?'\
             #IGNORE (formatting)
             '(?:\[((?:#\w+|dotted|dashed|bold|hidden)(?:,#\w+|,dotted|,dashed|,bold|,hidden)*)\])?'\
             # IGNORE(transition end ->), IGNORE (o maker)
             '(-*)\>(o[\s]+)?[\s]*'\
             # TDEST
             '([\w\.]+|[\w\.]+\[H\]|\[\*\]|\[H\]|(?:==+)(?:[\w\.]+)(?:==+))'\
             # <<IGNORE>>
             '[\s]*(\<\<.*\>\>)?[\s]*'\
             # hash words IGNORE
             '(#\w+)?(?:[\s]*)'\
             # TATTR
             '(?::[\s]*([^"\n]+))?(?:[\s]*)$',
                                 bygroups(TSOURCE,
                                          IGNORE,
                                          IGNORE, IGNORE, IGNORE,
                                          IGNORE,
                                          IGNORE,
                                          IGNORE,
                                          IGNORE, IGNORE,
                                          TDEST,
                                          IGNORE,
                                          IGNORE,
                                          TATTR),   ), #transition definition
            (# no group
             r'^state[\s]+'\
             # SALIAS as "STATE" |
             '(?:([\w\.]+)[\s]+as[\s]+["]([^"\n]+?)["]|'\
                # ("SALIAS" as) STATE
                 '(?:["]([^"\n]+?)["][\s]+as[\s]+)?([\w\.]+))'\
             # skip spaces
             '(?:[\s]*)'\
             # <<IGNORE>>, skip spaces,
             '(\<\<.*\>\>)?(?:[\s]*)'\
             # [["?\S"? non cap
             '(\[\['
                # trash inside brackets
                 '(?:["][^"]+["]|[^{}\s\]\[]*)'\
                 # skip spaces, {CALLBACK: embedded state} (want line returns)
                 '(?:[\s]*\{[\s]*(?:[^{}]+)\})?'\
                 # more trash
                 '(?:[\s]*(?:[^\]\[]+))?'\
             '\]\])?'\
             # skip space, hash words IGNORE, skip space
             '(?:[\s]*)(?:\w+[-\\|/]?\w+)?(?:[\s]*)'\
             # non-cap formatting, IGNORE
             '(?:##(?:\[(dotted|dashed|bold)\])?'\
                # IGNORE more formatting words?
                '(\w+)?)?'\
             # non-cap, now in embedded state
             '(?:[\s]*\{|[\s]+begin[\s]*)([^{}]+)(?:\}[\s]*)$',
                               bygroups(
                                        SALIAS, STATE,
                                        SALIAS, STATE,
                                        IGNORE,
                                        IGNORE,
                                        IGNORE, IGNORE,
                                        embedded_state
                               ), ),
            (r'^(?:[\s]*)(?:([\w\.]+)|["]([^"\n]+)["])'\
             '(?:[\s]*:[\s]*)'\
             '(.*)(?:[\s]*)$', bygroups(STATE, STATE, SATTR), ),
            (r'(?i)^(--+|\|\|+)$', IGNORE), # state delineation within superstate (-- or ||)
            # START note
            (r'^note[\s]+(right|left|top|bottom)(?:[\s]+of[\s]+([\w\.]+|["][^"\n]+["])|)[\s]*(#\w+[-\\|/]?\w+)?[\s]*\{?$', IGNORE, 'note'),
            (r'(?i)^(hide|show)[\s]+empty[\s]+description$', IGNORE),
            (r'^note[\s]+(right|left|top|bottom)(?:[\s]+of[\s]+([\w\.]+|["][^"\n]+["])|)[\s]*(#\w+[-\\|/]?\w+)?[\s]*:[\s]*(.*)$', IGNORE),
            (r'^note[\s]+(right|left|top|bottom)?[\s]*on[\s]+link[\s]*(#\w+[-\\|/]?\w+)?[\s]*:[\s]*(.*)$', IGNORE),
            # START note
            (r'^note[\s]+(right|left|top|bottom)?[\s]*on[\s]+link[\s]*(#\w+[-\\|/]?\w+)?$', IGNORE, 'note'),
            (r'(?i)^url[\s]*(?:of|for)?[\s]+([\w\.]+|["][^"\n]+["])[\s]+(?:is)?[\s]*(\[\[(["][^"\n]+["]|[^{}\s\]\[\n]*)(?:[\s]*\{([^{}\n]+)\})?(?:[\s]*([^\]\[\n]+))?\]\])$', IGNORE),
            (r'^note[\s]+["]([^"\n]+)["][\s]+as[\s]+([\w\.]+)[\s]*(#\w+[-\\|/]?\w+)?$', IGNORE),
            # START note
            (r'^(note)[\s]+as[\s]+([\w\.]+)[\s]*(#\w+[-\\|/]?\w+)?$', IGNORE, 'note'),
            # blank lines
            (r'(?i)^[\s]+$', IGNORE),
            # (r"(?i)^[\s]*(['].+||/['].+[']/[\s]*)$", IGNORE), # comment
            # START Comment
            (r"(?i)^[\s]*/['].*$", IGNORE, 'comment'),
            (r'(?i)^!pragma[\s]+([A-Za-z_][A-Za-z_0-9]*)(?:[\s]+(.*))?$', IGNORE, ), # pre-processor definitions
            (r'(?i)^title(?:[\s]*:[\s]*|[\s]+)(.*[\w\.].*)$', IGNORE, ), # diagram title
            # START title
            (r'(?i)^title$', IGNORE, 'title'),
            # START legend state
            (r'^legend(?:[\s]+(top|bottom))?(?:[\s]+(left|right|center))?$', IGNORE, 'legend'),

            (r'(?i)^(?:(left|right|center)?[\s]*)footer(?:[\s]*:[\s]*|[\s]+)(.*[\w\.].*)$', IGNORE, ),
            # START footer state
            (r'(?i)^(?:(left|right|center)?[\s]*)footer$', IGNORE, 'footer'),

            (r'(?i)^(?:(left|right|center)?[\s]*)header(?:[\s]*:[\s]*|[\s]+)(.*[\w\.].*)$', IGNORE, ),
            # START header state
            (r'(?i)^(?:(left|right|center)?[\s]*)header$', IGNORE, 'header'),
            (r'(?i)^(skinparam|skinparamlocked)[\s]+([\w.]*(?:\<\<.*\>\>)?[\w.]*)[\s]+([^{}]*)$', IGNORE, ),
            (r'BRACKET: (?i)^skinparam[\s]*(?:[\s]+([\w.]*(?:\<\<.*\>\>)?[\w.]*))?[\s]*\{$', IGNORE, ),
            (r'(?i)^minwidth[\s]+(\d+)$', IGNORE, ),
            (r'(?i)^rotate$', IGNORE, ),
            (r'(?i)^scale[\s]+([0-9.]+)(?:[\s]*/[\s]*([0-9.]+))?$', IGNORE, ),
            (r'(?i)^scale[\s]+([0-9.]+)[\s]*[*x][\s]*([0-9.]+)$', IGNORE, ),
            (r'(?i)^scale[\s]+([0-9.]+)[\s]+(width|height)$', IGNORE, ),

            (r'(?i)^!transformation[\s]+([^{}]*)$', IGNORE, ),
            # START transformation
            (r'(?i)^!transformation[\s]+\{[\s]*$', IGNORE, 'transformation'),
            (r'(?i)^(hide|show)[\s]+unlinked$', IGNORE, ),
            # START sprite state
            (r'^sprite[\s]+\$?([\w\.]+)[\s]*(?:\[(\d+)x(\d+)/(\d+)(z)?\])?[\s]*\{$', IGNORE, 'sprite'),
            (r'^sprite[\s]+\$?([\w\.]+)[\s]*(?:\[(\d+)x(\d+)/(\d+)(z)\])?[\s]+([-_A-Za-z0-9]+)$', IGNORE, ),
            (r'^sprite[\s]+\$?([\w\.]+)[\s]*[\s]+(.*)$', IGNORE, ),
            (r'^(hide|show)[\s]+((?:public|private|protected|package)?(?:[,\s]+(?:public|private|protected|package))*)[\s]+(members?|attributes?|fields?|methods?)$', IGNORE, ),
            (r'^(hide|show)[\s]+(?:(class|interface|enum|annotation|abstract|[\w\.]+|["][^"]+["]|\<\<.*\>\>)[\s]+)*?(?:(empty)[\s]+)?(members?|attributes?|fields?|methods?|circle\w*|stereotypes?)$', IGNORE, ),

            # Consume strip tags
            (r'^(@startuml|@enduml)$', IGNORE),
        ],

        'state': [
            include('root'),
            (r'(?i)^(end[\s]?state|\})$', IGNORE, '#pop'),
        ],

        'note': [
            include('root'),
            # END note
            (r'(?i)^(end[%s]?note|\})$', IGNORE, '#pop'),
            # END note
            (r'(?i)^end[%s]?note$', IGNORE, '#pop'),
            # END note
            (r'(?i)^end[%s]?note$', IGNORE, '#pop'),
        ],

        'comment': [
            include('root'),
            # END comment
            (r'(?i)^.*[%q]/[%s]*$', IGNORE, '#pop'),
        ],

        'title': [
            include('root'),
            # END tile
            (r'(?i)^end[%s]?title$', IGNORE, '#pop'),
        ],

        'legend': [
            include('root'),
            # END legend
            (r'(?i)^end[%s]?legend$', IGNORE, '#pop'),
        ],

        'footer': [
            include('root'),
            # END footer
            (r'(?i)^end[%s]?footer$', IGNORE, '#pop'),
        ],

        'header': [
            include('root'),
            # END header
            (r'(?i)^end[%s]?header$',IGNORE , '#pop'),
        ],

        'transformation': [
            include('root'),
            #END transformation
            (r'(?i)^[%s]*!\}[%s]*$', IGNORE, '#pop'),
        ],

        'sprite': [
            include('root'),
            #END sprite
            (r'(?i)^end[%s]?sprite|\}$', IGNORE, '#pop'),
        ],

    }


    def get_tokens_unprocessed(self, text, stack=('root',), debug = True, debug_regex=False):
        '''Catch-all for anything missed above'''
        pos = 0
        tokendefs = self._tokens
        statestack = list(stack)
        statetokens = tokendefs[statestack[-1]]

        #print tons of debugging if defined
        if debug_regex:
            for rexmatch, action, new_state in statetokens:
                rex = rexmatch.__self__
                print rex.pattern, '\n\t', rex.groups, '\t', rex.flags

        while 1:
            for rexmatch, action, new_state in statetokens:
                m = rexmatch(text, pos)

                if m:
                    if debug:
                        print "====================MATCH FOUND:========="
                        print stack
                        print m.re.pattern, len(m.string)
                        print "========================================="

                    if action is not None:
                        if type(action) is _TokenType:
                            yield pos, action, m.group()
                        else:
                            for item in action(self, m):
                                yield item
                    pos = m.end()
                    if new_state is not None:
                        # state transition
                        if isinstance(new_state, tuple):
                            for state in new_state:
                                if state == '#pop':
                                    statestack.pop()
                                elif state == '#push':
                                    statestack.append(statestack[-1])
                                else:
                                    statestack.append(state)
                        elif isinstance(new_state, int):
                            # pop
                            del statestack[new_state:]
                        elif new_state == '#push':
                            statestack.append(statestack[-1])
                        else:
                            assert False, "wrong state def: %r" % new_state
                        statetokens = tokendefs[statestack[-1]]
                    break
            else:
                try:
                    if text[pos] == '\n':
                        # at EOL, reset state to "root"
                        statestack = ['root']
                        statetokens = tokendefs['root']
                        yield pos, Text, u'\n'
                        pos += 1
                        continue
                    yield pos, Error, text[pos]
                    pos += 1
                except IndexError:
                    break


def preprocess_plantUML(file):
    '''functon to run plantUML pre-processor, returning straight plantUML text file'''
    pass

if __name__ == "__main__":
    from pygments.formatters import HtmlFormatter
    from pygments import lex

    # quick lexer test
    selected_lexer = puml_state_lexer()
    formatter = HtmlFormatter(style='vim', full=True, encoding='utf-8')

    with open('../PH_AL_A165.puml') as ftest:
        test_text = ftest.read().encode('utf-8')

    tkns = lex(test_text, selected_lexer)

    # with open('test_out.html', mode='w') as test_output:
    #     formatter.format(tokens, test_output)

    for tkn in tkns:
        if tkn != Error:
            print tkn

    print "Testing complete."




