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
Slowly ramp open the vent valve to ATM
'''


import tools.Utilities.Logger as Logger
dlog = Logger.LogTools('AttributeParser.log', 'AttributeParser')
dlog.Output2Stdout()
dlog.rootlog.warning('Module initialized')

import AttributeTypes as AT
from AttributeGrammar import action, compound_exp
from pyparsing import ParseException

class AST(object):
    '''Abstract syntax tree for deciding proper AttributeType subclass based on parsed attribute'''

    def __init__(self):
        self.logger = dlog.MakeChild('Attribute AST')
        self.root = AT.Attribute_Base

        self.datatypes = {
            'discrete'  : [AT.DiscreteAttribute,
                           AT.DiscreteCondition,
                           AT.PositionAttribute,
                           AT.StatusAttribute,
                           AT.ModeAttribute],
            'namedset'  : [AT.NamedDiscrete,
                           AT.EMCMDAttribute,
                           AT.PhaseCMDAttribute,
                           AT.StatusAttribute],
            'analog'    : [AT.AnalogAttribute,
                           AT.AnalogCondition,
                           AT.InicationAttribute,
                           AT.PositionAttribute,
                           AT.StatusAttribute,
                           AT.ModeAttribute],
            'prompt'    : [AT.PromptAttribute],
            'other'     : [AT.OtherAttribute]
        }



    def solve(self, parse_results):
        '''Solves for attribute type based on parser results
            Returns of list of AttributeType instances
        '''
        # action word will have underlying tag expressions
        if 'action_word' in parse_results:
            if any('open', 'close') in parse_results:
                pass

        # action phrases require varied arguments
        elif 'action_phrase' in parse_results:
            pass

    def resolve_tag(self, tag):
        '''
        Resolves attribute datatypes based on external configuration data
        :param tag: string tag to look up from DeltaV configuration
        :return:
            Type of tag referenced by input argument 'tag' - i.e. discrete, analog, position, etc.
        '''
        # discrete types
        if any(['CV', 'HS']) in tag:
            pass

class AttributeParser(object):
    '''
    Essentially an AttributeTypes instance factory when fed attribute strings
    '''

    def __init__(self, *args, **kwargs):
        '''Constructor'''
        self.diagram_id = kwargs.pop('id', 'Anywhere')
        self.logger = dlog.MakeChild('Parser')

        self.ast = AST()

    def parse(self, attribute_string):
        '''
        Generates attribute instances from a given attribute string
        :param attribute_string: string for a given state or transition attribute
        :return: AttributeType.Attribute_Base instance
        '''
        # Determine if keyword in first position
        self.logger.debug('Attempting to parse: \" %s \"', attribute_string)
        try:
            parse_result = action.parseString(attribute_string)
            self.logger.debug('\t %s', parse_result.dump())

        except ParseException, err:
            # no action word
            self.logger.debug("ERROR: No action word found in %s, parsing by expression", attribute_string)

            # Determine execution type by context:
            try:
                parse_result = compound_exp.parseString(attribute_string)
                self.logger.debug(parse_result.dump())
            except:
                self.logger.error('Unable to parse %s', attribute_string)
                parse_result = None

        return parse_result

    def create_attribute_instance(self, tag, raw_string):
        '''Creates a new attribute instance based on text parsing results.
            There should be a single attribute for each command or condition.'''
        self.logger.debug('Creating new attribute from %s as %s', raw_string, tag)
        pass

    def log2stdout(self):
        '''methods redirects all logging statements to stout'''
        self.logger.addHandler(Logger.logging.StreamHandler(Logger.stdout))


if __name__ == "__main__":

    test_strings = [
        "Open 'CV-2394'",
        "Set 'PIC-1899' to 100 in AUTO",
        "Open 'N2_VALVE' in Auto with a setpoint of 2 psig",
        "Open 'N2_VALVE' in auto SP 2psig",
        "Verify 'PIC-3851' > 125 F",
        "Check 'FIC-1795' is in Remote OUTput",
        "Wait until 'LI-398' is less than 100 lbs or 'FIC-2432' < 2.0 ",
        'ACK operator "Sodium Borohydride Charge is Completed"',
        "Wait 30 minutes",
        "'PIC-1899' := 100 in AUTO",
        "Read OPC '/TK15-CHG-EM/OP001.CV' '/TK50-CHG-EM/OP002'",
        "Verify 'PIC-1978' is remote out"
    ]

    parser = AttributeParser(); parser.log2stdout()

    results = list()
    for attr_str in test_strings:
        results.append(parser.parse(attr_str))


    print "=====Testing Complete====="