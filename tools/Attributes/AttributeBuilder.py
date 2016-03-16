'''
Module contains class definitions for a attribute builder.

The builder takes parsed attribute results and determines the appropriate attribute type
based on context from the raw attribute definition string and DeltaV configuration
facilitated by a DVConfigClient connection.
'''

from AttributeTypes import *
from DVConfigClient import DVConfigClient
from AttributeParser import AttributeParser

__author__ = 'ekopache'

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
        else:
            raise TypeError

    def connect_client(self):
        self.client.connect()

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
               tag = parse_results['tag']
            module_info = self.get_module_info(tag)
            # check if discrete module
            if '/'.join(['/', tag, 'PV_D']) in module_info['attribute_paths']:
                attr_list.append(PositionAttribute(tag, 'PV_D.CV'))
            else:
                attr_list.append(PositionAttribute(tag, 'PV.CV'))

        if 'expression' in parse_results:
            expressions = parse_results['expression']

            if 'condition' in expressions:
                condition_list = expressions['condition']
                for cnd in condition_list:
                    attr_list.append(self.generate_attribute(cnd), 'condition')

            if 'command' in expressions:
                command_list = expressions['command']
                for cmd in command_list:
                    attr_list.append(self.generate_attribute(cmd), 'command')


        return attr_list

    def generate_attribute(self, parse_dict, attribute_type):
        '''
        Generates the required AttributeType from a raw string
        :param raw_string: raw attribute string from plantUML diagram
        :return: AttributeType instance as required
        '''

        if attribute_type == 'condition':
            tag = parse_dict['tag']
            module_info = self.get_module_info(tag)
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
            tag = parse_dict['tag']
            module_info = self.get_module_info(tag)


    def get_module_info(self, tag):
        '''returns a dictionary of info for the module reference by tag'''
        return self.client.get_module_info(tag)


    def get_alias(self, tag, alias):
        '''Resolves aliases or shared module for the parent module defined by tag'''
        return self.client.get_alias(tag, alias)

    def check_tag_exists(self, tag):

    def get_PV(self, tag):
        '''returns tag to PV or PV_D as required'''

