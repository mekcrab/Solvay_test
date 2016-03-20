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
dlog = LogTools('ModelBuilder.log', 'AttributeBuilder')
dlog.rootlog.debug('Module initialized')


class AttributeBuilder(object):

    attr_dict = {
        'condition': Compare,
        'indicator': InicationAttribute,
        'constant': Constant,
        'mode': ModeAttribute,
        'command': PositionAttribute,
    }

    def __init__(self, parser, client, ):

        if isinstance(parser, AttributeParser):
            self.parser = parser
        else:
            raise TypeError

        if isinstance(client, DVConfigClient):
            self.client = client
            self.connect_client()
        else:
            raise TypeError

        self.logger = dlog.rootlog

    def connect_client(self):
        try:
            self.client.connect()
        except socket.error as err:
            print 'Could not connect client on ', self.client.address + ':' + self.client.port
            pass

    def disconnect_client(self):
        self.client.disconnect()

    def solve_attribute(self, raw_string):
        '''
        solves for what attributes should be generated from a raw string taken from the diagram
        :param raw_string:
        :return: list of AttributeType instance
        '''
        attr_list = list()
        parse_results = self.parser.parse(raw_string)

        if 'action_word' in parse_results:
            action = parse_results['action_word']

            if action in ['open', 'close']:
                self.logger.debug('Creating PositionAttribute ', action)
                self.generate_attribute(parse_results, 'position')

            elif action in ['write']:
                self.logger.debug("Adding write action", action)
                pass

            elif action in ['read']:
                self.logger.debug("Adding read action", action)
                pass

            elif action in ['prompt']:
                self.logger.debug("Adding prompt action", action)
                pass

            else:
                self.logger.error('Unknown action word: %s', action)

        if 'expression' in parse_results:
            expressions = parse_results['expression']

            if 'condition' in expressions:
                self.logger.debug("Adding condition")
                condition_list = expressions['condition']
                for cnd in condition_list:
                    attr_list.append(self.generate_attribute(cnd), 'condition')

            if 'command' in expressions:
                command_list = expressions['command']
                self.logger.debug("Adding command")
                for cmd in command_list:
                    attr_list.append(self.generate_attribute(cmd), 'command')

        return attr_list

    def generate_attribute(self, parse_dict, attribute_type):
        '''
        Generates the required AttributeType from a raw string
        :param raw_string: raw attribute string from plantUML diagram
        :return: AttributeType instance as required
        '''

        tag = self.parser.get_tag(parse_dict)

        # ===create no attribute if the tag is ignored===
        if tag == 'ignore':
            return
        else:
            module_info = self.get_module_info(tag)

        # ===== Attribute types by string name <attribute_type>======
        # todo: clean up - use separate method for generating each attribute type
        if attribute_type == 'condition':
            # check if discrete module
            if '/'.join(['/', tag, 'PV_D']) in module_info['attribute_paths']:
                lhs = DiscreteAttribute(tag, 'PV_D.CV')
            else:
                lhs = InicationAttribute(tag, 'PV.CV')

            value = parse_dict['value']
            try:
                rhs = Constant(float(value))
            # todo: handle secondary tag value
            except Exception as err:
                print str(err)
                raise

            return Compare(lhs, parse_dict['compare'], rhs)

        elif attribute_type == 'command':
            pass

        elif attribute_type == 'position':
            # check if discrete module
            if '/'.join(['/', tag, 'PV_D']) in module_info['attribute_paths']:
                attr_list.append(PositionAttribute(tag, 'PV_D.CV'))
            else:
                attr_list.append(PositionAttribute(tag, 'PV.CV'))



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
