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
        :return: list of AttributeType instance
        '''
        attr_list = list()
        parse_results = self.parser.parse(raw_string)

        if not parse_results:
            self.logger.error("Attribute string:: %s :: not parseable", raw_string)
            return attr_list

        if 'action_word' in parse_results:
            action = parse_results['action_word'].lower()

            if action in ['open', 'close']:
                self.logger.debug('Creating PositionAttribute %s', raw_string)
                attr_list.append(self.generate_attribute(parse_results, 'position'))

            elif action in ['wait']:
                self.logger.debug("Adding wait action: %s", raw_string)
                attr_list.append(self.generate_attribute(parse_results, 'compare'))

            elif action in ['read', 'write']:
                self.logger.debug("Adding read/write action: %s", raw_string)
                attr_list.append(self.generate_attribute(parse_results, 'compare'))

            elif action in ['prompt']:
                self.logger.debug("Adding prompt action: %s", raw_string)
                attr_list.append(self.generate_attribute(parse_results, 'prompt'))

            else:
                self.logger.error('Unknown action word: %s', raw_string)
                raise NameError

        # no action word found, check for attribute type by operator context
        elif 'expression' in parse_results:
            expressions = parse_results['expression']

            if 'condition' in expressions:
                self.logger.debug("Adding one or more conditions")
                condition_list = expressions['condition']
                for cnd in condition_list:
                    attr_list.append(self.generate_attribute(cnd), 'condition')

            elif 'condition' in parse_results:
                self.logger.debug("Adding single condition")
                attr_list.append(self.generate_attribute(parse_results.condition, 'condition'))

            if 'command' in expressions:
                command_list = expressions['command']
                self.logger.debug("Adding command")
                for cmd in command_list:
                    attr_list.append(self.generate_attribute(cmd), 'command')

        else:
            self.logger.error("No attribute types found in %s", raw_string)

        return attr_list

    def generate_attribute(self, parse_dict, attribute_type):
        '''
        Generates the required AttributeType from a raw string
        :param raw_string: raw attribute string from plantUML diagram
        :return: AttributeType instance as required
        '''
        try:
            tag = self.parser.get_tag(parse_dict)
        except:
            self.logger.warning("Falling back to default tag to generate %s attribute", attribute_type)
            tag = self.default_tag

        # ===create no attribute if the tag is ignored===
        if tag == 'ignore':
            return
        else:
            module_info = self.get_module_info(tag)

        # ===== Attribute types by string name <attribute_type>======
        if attribute_type == 'path':
            # check for path
            if 'path' in parse_dict:
                return OtherAttribute(tag, parse_dict['path'])
            # no path found, assume PV
            elif '/'.join(['/', tag, 'PV_D']) in module_info['attribute_paths']:
                return DiscreteAttribute(tag, 'PV_D.CV')
            elif '/'.join(['/', tag, 'PV']) in module_info['attribute_paths']:
                return InicationAttribute(tag, 'PV.CV')
            else:
                self.logger.error("No path found in parsed expression %s", parse_dict)

        elif attribute_type == 'prompt':
            # get target from diagram
            if 'value' in parse_dict: target = parse_dict['value']
            else: self.logger.warning("No target found in prompt, defaulting to 0"); target = 0;
            # look for message in diagram
            message_string = parse_dict.asList()[1]
            # determine if tag is for EM or phase
            if 'EM' in tag[0:1]:
                message_path = 'MSG2'
                response_path = 'MONITOR/OAR/DATA_IN'
            elif 'PH' in tag[0:1]:
                raise NotImplementedError
            else:
                self.logger.error("Undefined prompt from parsed expression ", parse_dict)

            return PromptAttribute(tag, target, message_string, message_path, response_path)

        elif attribute_type == 'position':
            # check if discrete module
            if '/'.join(['/', tag, 'PV_D']) in module_info['attribute_paths']:
                return PositionAttribute(tag, 'PV_D.CV')
            # otherwise return analog type
            else:
                return PositionAttribute(tag, 'PV.CV')

        elif attribute_type == 'condition':
            lhs = self.generate_attribute(parse_dict['lhs'], 'path')
            rhs = self.generate_attribute(parse_dict['rhs'], 'path')
            return Compare(lhs, parse_dict['compare'], rhs)

        elif attribute_type == 'command':
            raise NotImplementedError

    def get_module_info(self, tag):
        '''returns a dictionary of info for the module reference by tag'''
        return self.client.get_module_info(tag)


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
        attr_list = abuilder.solve_attribute(attr_str)
        pp([(attr, attr.__dict__) for attr in attr_list])
