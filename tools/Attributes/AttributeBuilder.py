'''
Module contains class definitions for a attribute builder.

The builder takes parsed attribute results and determines the appropriate attribute type
based on context from the raw attribute definition string and DeltaV configuration
facilitated by a DVConfigClient connection.
'''

from AttributeTypes import *
import socket

from DVConfigClient import DVConfigClient
from AttributeParser import AttributeParser

__author__ = 'ekopache'


from tools.Utilities.Logger import LogTools
dlog = LogTools('AttributeBuilder.log', 'AttributeBuilder')
dlog.rootlog.debug('Module initialized')


def isNumber(raw_string):
    '''Checks if string can be converted to a number'''
    try:
        float(raw_string)
        return True
    except:
        return False

def isString(raw_string):
    '''Checks if the raw string is surrounded by double quotes'''
    if raw_string[0] == raw_string[-1] == '\"':
        return True
    else:
        return False

class AttributeBuilder(object):

    def __init__(self, parser, client, default_tag=''):

        if isinstance(parser, AttributeParser):
            self.parser = parser
        else:
            raise TypeError

        if isinstance(client, DVConfigClient):
            self.client = client
            self.connect_client()
        else:
            raise TypeError

        self.logger = dlog.MakeChild('AttributeBuilder')
        self.default_tag = default_tag  # default tag for the diagram in question

    def connect_client(self):
        try:
            self.client.connect()
        except socket.error as err:
            self.logger.error('Could not connect client on %s:%s', self.client.address, self.client.port)

    def disconnect_client(self):
        self.client.disconnect()

    def set_default_tag(self, tag):
        '''Sets a default tag for this diagram'''
        self.default_tag = tag

    def solve_attribute(self, raw_string):
        '''
        solves for what attributes should be generated from a raw string taken from the diagram
        :param raw_string:
        :return: AttributeType instance
        '''
        #TODO: expand to handle compound expressions and multiple attributes in a single raw string

        parse_results = self.parser.parse(raw_string)

        if not parse_results:
            self.logger.error("Attribute string:: %s :: not parseable, return raw string", raw_string)
            return raw_string
        try:
            if 'action_word' in parse_results:
                action = parse_results['action_word'].lower()

                if action in ['open', 'close']:
                    self.logger.debug('Creating PositionAttribute %s', raw_string)
                    new_attribute = self.generate_attribute(parse_results, 'position')

                elif action in ['wait']:
                    self.logger.debug("Adding wait action: %s", raw_string)
                    new_attribute = self.generate_attribute(parse_results, 'compare')

                elif action in ['read', 'write']:
                    self.logger.debug("Adding read/write action: %s", raw_string)
                    new_attribute = self.generate_attribute(parse_results, 'compare')

                elif action in ['prompt']:
                    self.logger.debug("Adding prompt action: %s", raw_string)
                    new_attribute = self.generate_attribute(parse_results, 'prompt')

                else:
                    self.logger.error('Unknown action word: %s', raw_string)
                    raise NameError

            elif 'action_phrase' in parse_results:
                action = parse_results['action_phrase']

                if action in ['prompt']:
                    self.logger.debug("Adding prompt phrase: %s", raw_string)
                    new_attribute = self.generate_attribute(parse_results, 'prompt')

            # no action word found, check for attribute type by operator context
            elif 'expression' in parse_results:
                expressions = parse_results['expression']

                if 'condition' in parse_results:
                    self.logger.debug("Adding single condition")
                    new_attribute = self.generate_attribute(parse_results.condition, 'condition')

                elif 'command' in expressions:
                    command_list = expressions['command']
                    self.logger.debug("Adding command")
                    for cmd in command_list:
                        new_attribute=(self.generate_attribute(cmd), 'command')

            else:
                self.logger.error("No attribute types found in %s", raw_string)
                raise TypeError

        except StandardError:
            self.logger.debug("Attribute ignored: %s", raw_string)
            new_attribute = AttributeDummy()

        return new_attribute

    def generate_attribute(self, parse_dict, attribute_type):
        '''
        Generates the required AttributeType from a raw string
        :param raw_string: raw attribute string from plantUML diagram
        :return: AttributeType instance as required
        '''

        # ===== Attribute types by string name <attribute_type>======
        if attribute_type == 'path':
            tag, module_info = self.get_module_info(parse_dict)
            # check for path
            if 'path' in parse_dict:
                return OtherAttribute(tag, parse_dict['path'])
            # no path found, assume PV
            elif '/'.join(['/', tag, 'PV_D']) in module_info['attribute_paths']:
                return DiscreteAttribute(tag, 'PV_D.CV')
            elif '/'.join(['/', tag, 'PV']) in module_info['attribute_paths']:
                return IndicationAttribute(tag, 'PV.CV')
            else:
                self.logger.error("No path found in parsed expression %s", parse_dict)

        elif attribute_type == 'prompt':
            # get target from diagram
            if 'target' in parse_dict: target = parse_dict['target']
            else: self.logger.warning("No target found in prompt, defaulting to 0"); target = 0;

            # look for message in diagram
            if 'message' in parse_dict: message_string = parse_dict['message']
            else: self.logger.warning("No message found in prompt, defaulting to 'MESSAGE'"); message_string = "MESSAGE";

            # determine if tag is for EM or phase - you cannot have prompts for another test in this unit
            tag = self.default_tag
            if 'EM' in tag:  # fixme: this could be a nasty bug later
                message_path = 'MSG2'
                response_path = 'MONITOR/OAR/DATA_IN'
            elif 'PH' in tag[0:1]:
                raise NotImplementedError
            else:
                self.logger.error("Undefined prompt from parsed expression %s", parse_dict)

            return PromptAttribute(tag, target, message_string, message_path, response_path)

        elif attribute_type == 'position':
            tag, module_info = self.get_module_info(parse_dict)
            # check if discrete module
            if '/'.join(['/', tag, 'PV_D']) in module_info['attribute_paths']:
                return PositionAttribute(tag, 'PV_D.CV')
            # otherwise return analog type
            else:
                return PositionAttribute(tag, 'PV.CV')

        elif attribute_type in ['condition', 'compare']:
            lhs = self.generate_attribute(parse_dict['lhs'], 'path')
            # Check for string type
            rhs = parse_dict['rhs'][0]
            if isString(rhs):
                rhs = Constant(rhs.strip('\"'))
            elif isNumber(rhs):
                rhs = Constant(float(rhs))
            else:
                rhs = self.generate_attribute(parse_dict['rhs'], 'path')

            return Compare(lhs, parse_dict['compare'], rhs)

        elif attribute_type == 'command':
            raise NotImplementedError  # note this is different from NotImplemented

        else:
            self.logger.error("No attribute generated from %s", parse_dict)

    def get_module_info(self, parse_dict):
        '''returns a dictionary of info for the module reference by tag'''
        try:
            tag = self.parser.get_tag(parse_dict)
            # ===create no attribute if the tag is ignored===
            if 'ignore' in tag:
                self.logger.info("Ignoring %s", parse_dict)
                raise StandardError
        except AttributeError: # tag not found in parse_dict
            self.logger.warning("Falling back to default tag to generate attribute from %s", parse_dict)
            tag = self.default_tag

        return tag, self.client.get_module_info(tag)


    def get_alias(self, tag, alias):
        '''Resolves aliases or shared module for the parent module defined by tag'''
        return self.client.get_alias(tag, alias)

    def check_tag_exists(self, tag):
        pass

    def get_PV(self, tag):
        '''returns tag to PV or PV_D as required'''
        pass


def create_attribute_builder(server_ip='127.0.0.1', server_port=5489):
    '''
    Returns a attribute builder pre-configured with parser and DVConfigClient
    '''

    parser = AttributeParser()
    config_client = DVConfigClient(address=server_ip, port=server_port)
    attribute_builder = AttributeBuilder(parser, config_client)

    return attribute_builder

if __name__ == "__main__":
    import AttributeParser
    import DVConfigClient
    from pprint import pprint as pp

    test_attrs = [
         u'OAR Message: "enter charge amount in lbs"',
         u"Close 'CV-4289'",
         u"Set 'R10-WTRCHG-EM/OP001' = RCP_TGT",
         u"Close 'CV-4289'",
         u"Set 'R10-WTRCHG-EM/OP001' to 1000",
         u"Open 'CV-4289'",
         u"Set 'FQIC-4289/TOTAL' = 0",
         u"Set 'R10-WTRCHG-EM/OP001' = 0",
         u"Set 'ignore' = 0",
        ]

    abuilder = create_attribute_builder()

    LogTools.Output2Stdout(dlog, 'debug')

    for attr_str in test_attrs:
        new_attribute = abuilder.solve_attribute(attr_str)
        pp([(attr, attr.__dict__) for attr in new_attribute])
