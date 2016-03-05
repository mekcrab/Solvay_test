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


import tools.Utilities.Logger as Logger
dlog = Logger.LogTools('AttributeParser.log', 'AttributeParser')
dlog.rootlog.warning('Module initialized')

import AttributeTypes
from AttributeGrammar import action, compound_exp


class AttributeParser(object):
    '''
    Essentially an AttributeTypes instance factory when fed attribute strings
    '''

    def __init__(self, *args, **kwargs):
        '''Constructor'''
        self.diagram_id = kwargs.pop('id', 'Anywhere')
        self.logger = dlog.MakeChild('Parser', self.diagram_id)

    def parse(self, attribute_string):
        '''
        Generates attribute instances from a given attribute string
        :param attribute_string: string for a given state or transition attribute
        :return: AttributeType.Attribute_Base instance
        '''
        attribute_list = list()  # list of attributes matched from expression parsing
        # Determine if keyword in first position
        self.logger.debug("Attempting to parse: \"" + attribute_string + "\"")
        try:
            parse_result = action.parseString(attribute_string)
            self.logger.debug('\t', parse_result.dump())

        except pp.ParseException, err:
            # no action word
            self.logger.debug("ERROR: No action word found in %s, parsing by expression", attribute_string)

            # Determine execution type by context:
            parse_result = compound_exp.parseString(attribute_string)
            self.logger.debug(parse_result.dump())

        # resolve tag type from DeltaV


        # return attribute instance list
        return attribute_list

    def create_attribute_instance(self, tag, attr_type=None):
        '''Creates a new attribute instance based on text parsing results'''
        self.logger.debug('Creating new attribute from %s as %s', tag, attr_type)
        if attr_type:
            pass
        else:
            return AttributeTypes.Attribute_Base(tag)

    def resolve_tag(self, tag):
        '''

        :param tag: string tag to look up from DeltaV configuration
        :return:
            Type of tag referenced by input argument 'tag' - i.e. discrete, analog, position, etc.
        '''
        pass


if __name__ == "__main__":

    test_strings = [
        "Open 'CV-2394'",
        "Set 'PIC-1899' to 100 in AUTO",
        "Open 'N2_VALVE' in Auto with a setpoint of 2 psig",
        "Open 'N2_VALVE' in auto SP 2psig",
        "Verify 'PIC-3851' > 125 F",
        "Check 'FIC-1795' is in ROUT",
        "Wait until 'LI-398' is less than 100 lbs or 'FIC-2432' < 2",
        'ACK operator "Sodium Borohydride Charge is Completed"',
        "Wait 30 minutes",
        "'PIC-1899' := 100 in AUTO",
        "Read OPC '/TK15-CHG-EM/OP001.CV' '/TK50-CHG-EM/OP002'"
    ]

    parser = AttributeParser()
    dlog.Output2Stdout(level='info')

    for attr_str in test_strings:
        parser.parse(attr_str)

    print "=====Testing Complete====="
