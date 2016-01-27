'''
Python module for lexing plantUML state diagrams.
'''
__author__ = 'ekopache'

from pygments.lexer import RegexLexer, bygroups, include
from pygments.token import Name, Text

# token definitions

STATE = Name.Class  # state definition
SATTR = Name.Attribute # state attribute
SNOTE = Name.Label # state notes

TSOURCE = Name.Variable # transition source
TDEST = Name.Entity # transition destination
TATTR = Name.Other # transition attribute

IGNORE = Text # stuff to ignore

class puml_state_lexer(RegexLexer):

    # regex mode flags
    # flags = re.XXX    # (not used)

    tokens = {

        'root': [
            (r'(?i)^(hide|show)?[\s ]*footbox$', IGNORE),
            (r'(?i)^(left[\s ]to[\s ]right|top[\s ]to[\s ]bottom)[\s ]+direction$', IGNORE),
            (r'^(?:state[\s ]+)(?:([\p{L}0-9_.]+)[\s ]+as[\s ]+["“”«»]([^"“”«»]+)["“”«»]|["“”«»]([^"“”«»]+)["“”«»][\s ]+as[\s ]+([\p{L}0-9_.]+)|([\p{L}0-9_.]+)|["“”«»]([^"“”«»]+)["“”«»])[\s ]*(\<\<.*\>\>)?[\s ]*(\[\[(["“”«»][^"“”«»]+["“”«»]|[^{}\s \]\[]*)(?:[\s ]*\{([^{}]+)\})?(?:[\s ]*([^\]\[]+))?\]\])?[\s ]*(#\w+[-\\|/]?\w+)?[\s ]*(?:##(?:\[(dotted|dashed|bold)\])?(\w+)?)?[\s ]*(?::[\s ]*(.*))?$', IGNORE, 'state'),            (r'^([\p{L}0-9_.]+|[\p{L}0-9_.]+\[H\]|\[\*\]|\[H\]|(?:==+)(?:[\p{L}0-9_.]+)(?:==+))[\s ]*(\<\<.*\>\>)?[\s ]*(#\w+)?[\s ]*(x)?(-+)(?:\[((?:#\w+|dotted|dashed|bold|hidden)(?:,#\w+|,dotted|,dashed|,bold|,hidden)*)\])?(left|right|up|down|le?|ri?|up?|do?)?(?:\[((?:#\w+|dotted|dashed|bold|hidden)(?:,#\w+|,dotted|,dashed|,bold|,hidden)*)\])?(-*)\>(o[\s ]+)?[\s ]*([\p{L}0-9_.]+|[\p{L}0-9_.]+\[H\]|\[\*\]|\[H\]|(?:==+)(?:[\p{L}0-9_.]+)(?:==+))[\s ]*(\<\<.*\>\>)?[\s ]*(#\w+)?[\s ]*(?::[\s ]*([^"“”«»]+))?$', STATE),
            (r'^state[\s ]+(?:([\p{L}0-9_.]+)[\s ]+as[\s ]+["“”«»]([^"“”«»]+)["“”«»]|(?:["“”«»]([^"“”«»]+)["“”«»][\s ]+as[\s ]+)?([\p{L}0-9_.]+))[\s ]*(\<\<.*\>\>)?[\s ]*(\[\[(["“”«»][^"“”«»]+["“”«»]|[^{}\s \]\[]*)(?:[\s ]*\{([^{}]+)\})?(?:[\s ]*([^\]\[]+))?\]\])?[\s ]*(#\w+[-\\|/]?\w+)?[\s ]*(?:##(?:\[(dotted|dashed|bold)\])?(\w+)?)?(?:[\s ]*\{|[\s ]+begin)$', IGNORE, 'state'),
            (r'(?i)^(end[\s ]?state|\})$', IGNORE, '#pop'),
            (r'^(?:([\p{L}0-9_.]+)|["“”«»]([^"“”«»]+)["“”«»])[\s ]*:[\s ]*(.*)$', SATTR),
            (r'(?i)^(--+|\|\|+)$', IGNORE), # state delineation within superstate
            # START note
            (r'^note[\s +(right|left|top|bottom)(?:[\s ]+of[\s ]+([\p{L}0-9_.]+|["“”«»][^"“”«»]+["“”«»])|)[\s ]*(#\w+[-\\|/]?\w+)?[\s ]*\{?$', IGNORE, 'note'),
            (r'(?i)^(hide|show)[\s ]+empty[\s ]+description$', IGNORE),
            (r'^note[\s ]+(right|left|top|bottom)(?:[\s ]+of[\s ]+([\p{L}0-9_.]+|["“”«»][^"“”«»]+["“”«»])|)[\s ]*(#\w+[-\\|/]?\w+)?[\s ]*:[\s ]*(.*)$', IGNORE),
            (r'^note[\s ]+(right|left|top|bottom)?[\s ]*on[\s ]+link[\s ]*(#\w+[-\\|/]?\w+)?[\s ]*:[\s ]*(.*)$', IGNORE),
            # START note
            (r'^note[\s ]+(right|left|top|bottom)?[\s ]*on[\s ]+link[\s ]*(#\w+[-\\|/]?\w+)?$', IGNORE, 'note'),
            (r'(?i)^url[\s ]*(?:of|for)?[\s ]+([\p{L}0-9_.]+|["“”«»][^"“”«»]+["“”«»])[\s ]+(?:is)?[\s ]*(\[\[(["“”«»][^"“”«»]+["“”«»]|[^{}\s \]\[]*)(?:[\s ]*\{([^{}]+)\})?(?:[\s ]*([^\]\[]+))?\]\])$', IGNORE),
            (r'^note[\s ]+["“”«»]([^"“”«»]+)["“”«»][\s ]+as[\s ]+([\p{L}0-9_.]+)[\s ]*(#\w+[-\\|/]?\w+)?$', IGNORE),
            # START note
            (r'^(note)[\s ]+as[\s ]+([\p{L}0-9_.]+)[\s ]*(#\w+[-\\|/]?\w+)?$', IGNORE, 'note'),
            # blank lines
            (r'(?i)^[\s ]*$', IGNORE),
            (r"(?i)^[\s ]*(['‘’].*||/['‘’].*['‘’]/[\s ]*)$", IGNORE), # comment
            # START Comment
            (r"(?i)^[\s ]*/['‘’].*$", IGNORE, 'comment'),
            (r'(?i)^!pragma[\s ]+([A-Za-z_][A-Za-z_0-9]*)(?:[\s ]+(.*))?$', IGNORE, ), # pre-processor definitions
            (r'(?i)^title(?:[\s ]*:[\s ]*|[\s ]+)(.*[\p{L}0-9_.].*)$', IGNORE, ), # diagram title
            # START title
            (r'(?i)^title$', IGNORE, 'title'),
            # legend state
            (r'START: ^legend(?:[\s ]+(top|bottom))?(?:[\s ]+(left|right|center))?$', IGNORE, ),
            (r'(?i)^(?:(left|right|center)?[\s ]*)footer(?:[\s ]*:[\s ]*|[\s ]+)(.*[\p{L}0-9_.].*)$', IGNORE, ),
            # footer state
            (r'START: (?i)^(?:(left|right|center)?[\s ]*)footer$', IGNORE, ),
            (r'(?i)^(?:(left|right|center)?[\s ]*)header(?:[\s ]*:[\s ]*|[\s ]+)(.*[\p{L}0-9_.].*)$', IGNORE, ),
            (r'START: (?i)^(?:(left|right|center)?[\s ]*)header$', IGNORE, ),
            (r'(?i)^(skinparam|skinparamlocked)[\s ]+([\w.]*(?:\<\<.*\>\>)?[\w.]*)[\s ]+([^{}]*)$', IGNORE, ),
            (r'BRACKET: (?i)^skinparam[\s ]*(?:[\s ]+([\w.]*(?:\<\<.*\>\>)?[\w.]*))?[\s ]*\{$', IGNORE, ),
            (r'(?i)^minwidth[\s ]+(\d+)$', IGNORE, ),
            (r'(?i)^rotate$', IGNORE, ),
            (r'(?i)^scale[\s ]+([0-9.]+)(?:[\s ]*/[\s ]*([0-9.]+))?$', IGNORE, ),
            (r'(?i)^scale[\s ]+([0-9.]+)[\s ]*[*x][\s ]*([0-9.]+)$', IGNORE, ),
            (r'(?i)^scale[\s ]+([0-9.]+)[\s ]+(width|height)$', IGNORE, ),

            (r'(?i)^!transformation[\s ]+([^{}]*)$', IGNORE, ),
            (r'START: (?i)^!transformation[\s ]+\{[\s ]*$', IGNORE, ),
            (r'(?i)^(hide|show)[\s ]+unlinked$', IGNORE, ),
            # sprite state
            (r'START: ^sprite[\s ]+\$?([\p{L}0-9_]+)[\s ]*(?:\[(\d+)x(\d+)/(\d+)(z)?\])?[\s ]*\{$', IGNORE, ),
            (r'^sprite[\s ]+\$?([\p{L}0-9_]+)[\s ]*(?:\[(\d+)x(\d+)/(\d+)(z)\])?[\s ]+([-_A-Za-z0-9]+)$', IGNORE, ),
            (r'^sprite[\s ]+\$?([\p{L}0-9_]+)[\s ]*[\s ]+(.*)$', IGNORE, ),
            (r'^(hide|show)[\s ]+((?:public|private|protected|package)?(?:[,\s ]+(?:public|private|protected|package))*)[\s ]+(members?|attributes?|fields?|methods?)$', IGNORE, ),
            (r'^(hide|show)[\s ]+(?:(class|interface|enum|annotation|abstract|[\p{L}0-9_.]+|["“”«»][^"“”«»]+["“”«»]|\<\<.*\>\>)[\s ]+)*?(?:(empty)[\s ]+)?(members?|attributes?|fields?|methods?|circle\w*|stereotypes?)$', IGNORE, ),
        ],

        'state': [
            include('root'),
            # note lexer state?
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
            (r'END: (?i)^end[%s]?legend$', IGNORE, '#pop'),
        ],

        'footer': [
            include('root'),
            # END footer
            (r'(?i)^end[%s]?footer$', IGNORE, ),
        ],

        'header': [
            include('root'),
            # END header
            (r'END: (?i)^end[%s]?header$',IGNORE , '#pop'),
        ],

        'transformation': [
            include('root'),
            #END transformation
            (r'END: (?i)^[%s]*!\}[%s]*$', IGNORE, '#pop'),
        ],

        'sprite': [
            include('root'),
            #END sprite
            (r'END: (?i)^end[%s]?sprite|\}$', IGNORE, ),
        ],

    }

    def get_tokens_unprocessed(self, text, stack=('root',)):
        '''Catch-all for anything missed above'''
        for index, token, value in RegexLexer.get_tokens_unprocessed(self, text):
            yield index, token, value


if __name__ == "__main__":
    from pygments.formatters import HtmlFormatter
    from pygments import lex

    # quick lexer test
    lexer = puml_state_lexer()
    formatter = HtmlFormatter(style='vim', full=True, encoding='utf-8')

    with open('../interlock.puml') as ftest:
        test_text = ftest.read()

    tokens = lex(test_text, lexer)

    with open('test_out.html', mode='w') as test_output:
        formatter.format(tokens, test_output)

    print "Testing complete."




