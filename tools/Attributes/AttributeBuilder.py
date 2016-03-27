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
    if len(raw_string) > 1 and raw_string[0] == raw_string[-1] == '\"':
            return True
    else:
        return False

class AttributeIgnored(Exception):
    '''Custom exception used when attributes (or attributes-within-attributes like comparisons) are ignored'''
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, args, kwargs)


class AttributeBuilder(object):

    def __init__(self, parser, client, default_tag='', abort_on_error=False):

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

        # parsing option flags
        self.abort_on_error = abort_on_error  # fails program on parsing/instansiation errors

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

    def attribute_building_error(self, raw_string):
        '''
        :param raw_string: string definition of attribute from puml diagram
        Raises error when unable to create an AttributeType instance.
        Error passes silently if self.abort_on_error is True.
        '''
        self.logger.error("No attribute types found in %s", raw_string)
        if self.abort_on_error:
            raise TypeError
        else:
            print self.parser.parse(raw_string).dump()
        return raw_string

    def solve_attribute(self, raw_string):
        '''
        Solves for what attributes should be generated from a raw string taken from the diagram
        :param raw_string: attribute string definition from diagram
        :return: new_attribute: AttributeType instance or raw_string on failure to produce attribute
        '''
        #TODO: expand to handle compound expressions and multiple attributes in a single raw string

        parse_results = self.parser.parse(raw_string)

        if not parse_results:
            self.logger.error("Attribute string:: %s :: not parseable, return raw string", raw_string)
            return raw_string

        new_attribute = None

        try:
            if 'action_word' in parse_results:
                action = parse_results['action_word'].lower()

                if action in ['open', 'close', 'start', 'stop']:
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
                # TODO: expressions = parse_results['expression'] for multiple attributes in given string
                if 'condition' in parse_results:
                    self.logger.debug("Adding single condition from %s", raw_string)
                    new_attribute = self.generate_attribute(parse_results.condition, 'condition')

                elif 'command' in parse_results:
                    self.logger.debug("Adding command")
                    new_attribute = self.generate_attribute(parse_results.command, 'command')

        except AttributeIgnored as err:  # AttributeIgnored raised when attribute is to be disregarded
            self.logger.debug("Attribute ignored: %s", raw_string)
            new_attribute = AttributeDummy(raw_string)

        # return new AttributeType if possible
        if new_attribute:
            return new_attribute
        else:
            return self.attribute_building_error(raw_string)

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
                return DiscreteAttribute(tag, attr_path='PV_D')
            elif '/'.join(['/', tag, 'PV']) in module_info['attribute_paths']:
                return IndicationAttribute(tag, attr_path='PV')
            elif 'value' in parse_dict:
                return self.generate_attribute(parse_dict, 'value')
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
            if 'EM' in tag:  # fixme: this could be a nasty bug later should EM naming conventions change...
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
                # fixme: taget_value should be obtained from configuration
                return PositionAttribute(tag, attr_path='PV_D.CV', target_value=0)
            # otherwise return analog type
            else:
                # fixme: taget_value should be obtained from from context of action word
                return PositionAttribute(tag, attr_path='PV.CV', taget_value=0)

        elif attribute_type in ['condition', 'compare']:
            tag, module_info = self.get_module_info(parse_dict.lhs)
            lhs = self.generate_attribute(parse_dict['lhs'], 'path')
            # Check for string type
            rhs = parse_dict.rhs
            if 'path' in rhs:
                rhs = self.generate_attribute(parse_dict['rhs'], 'path')
            elif 'value' in rhs:
                rhs = rhs.value[0]
                if type(rhs) in [str, unicode] and isString(rhs):
                    rhs = Constant(rhs.strip('\"'))
                elif isNumber(rhs):
                    rhs = Constant(float(rhs))
                else:  # path is based on lhs tag
                    parse_dict['rhs']['tag'] = tag
                    rhs = self.generate_attribute(parse_dict['rhs'], 'path')

            return Compare(lhs, parse_dict['compare'], rhs)

        elif attribute_type == 'command':
            if 'rhs' in parse_dict:  # path attribute in command,
                raise NotImplementedError
            elif 'value' in parse_dict:
                return self.generate_attribute(parse_dict, 'value')

        elif attribute_type == 'value':
            command_vals = {'trip': InterlockAttribute,
                            'reset': InterlockAttribute,
                            'open': PositionAttribute,
                            'close': PositionAttribute,
                            'start': NamedDiscrete,
                            'stop': NamedDiscrete
                            }
            if 'value' in parse_dict:

                val = parse_dict.value[0]

                self.logger.debug("Generating attribute from value: %s", val)

                if val in ['open', 'close']:
                    new_attr = self.generate_attribute(parse_dict, 'position')
                    # fixme - dirty fix to get thing going
                    if val == 'open':
                        new_attr.set_target_value(1)
                    elif val == 'close':
                        new_attr.set_target_value(0)
                    else:
                        self.logger.error("No target value found, cannot set in %s", new_attr)
                    return new_attr
                elif val in ['trip', 'reset']:
                    attr_class = command_vals[val]
                    self.logger.debug("Creating %s from: %s", attr_class.__name__, ' '.join(parse_dict.asList()))
                    return attr_class(parse_dict.tag, val)
                elif val in ['start', 'stop']:
                    self.logger.error("===>Need to implement motors for ", parse_dict.tag)
                    return AttributeDummy
                elif isString(val):
                    return Constant(val.string('\"'))
                elif isNumber(val):
                    return Constant(float(val))

        else:
            self.logger.error("No attribute generated from %s", parse_dict)

    def get_module_info(self, parse_dict):
        '''returns a dictionary of info for the module reference by tag'''
        try:
            tag = self.parser.get_tag(parse_dict)
            # ===create no attribute if the tag is ignored===
            if 'ignore' in tag:
                self.logger.debug("Ignoring %s", parse_dict)
                raise AttributeIgnored
        except AttributeError: # tag not found in parse_dict
            self.logger.warning("Falling back to default tag to generate attribute from %s", parse_dict)
            tag = self.default_tag

        return tag, self.client.get_module_info(tag)

    def get_alias(self, tag, alias):
        '''Resolves aliases or shared module for the parent module defined by tag'''
        return self.client.get_alias(tag, alias)

    def get_namedset(self, namedset):
        '''Returns a dictionary of namedset {entry string: integer value}'''
        return self.client.get_namedset(namedset)

    def check_tag_exists(self, tag):
        raise NotImplementedError

    def get_PV(self, tag):
        '''Returns tag to PV or PV_D as required'''
        raise NotImplementedError


def create_attribute_builder(server_ip='127.0.0.1', server_port=5489):
    '''
    Returns a attribute builder pre-configured with parser and DVConfigClient
    '''
    from DVConfigClient import DVConfigClient
    from AttributeParser import AttributeParser

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
        attr_inst = abuilder.solve_attribute(attr_str)
        pp([(attr, attr.__dict__) for attr in attr_inst])
