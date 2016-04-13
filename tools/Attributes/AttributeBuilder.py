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
    print len(raw_string), raw_string[0], raw_string[-1]
    if len(raw_string) > 1 and raw_string[0] == raw_string[-1] == "\'":
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
            self.logger.error("Attribute string:: %s :: not parsed, returning raw string", raw_string)
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
                #
                # elif action in ['write']:
                #     self.logger.debug("Adding write action: %s", raw_string)
                #     if 'value' in parse_results:
                #         new_attribute = self.generate_attribute(parse_results, 'value')
                #     elif 'path' in parse_results:
                #         new_attribute = self.generate_attribute(parse_results, 'path')
                #     elif 'compare' in parse_results:
                #         new_attribute = self.generate_attribute(parse_results, 'compare')
                #     else:
                #         self.logger.error("Unknown attribute generation for %s", raw_string)

                elif action in ['read', 'write']:
                    self.logger.debug("Adding read/write action: %s", raw_string)
                    if 'compare' in parse_results:
                        new_attribute = self.generate_attribute(parse_results, 'compare')
                    elif 'value' in parse_results:
                        new_attribute = self.generate_attribute(parse_results, 'value')
                    else:
                        self.logger.error("Unknown attribute generation for %s", raw_string)

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
            self.logger.debug('Generating path attribute from %s', parse_dict.dump())
            tag, module_info = self.get_module_info(parse_dict)
            # check for path
            if 'value' in parse_dict or parse_dict.value:
                print "path parse_dict value:", parse_dict.value
                return self.generate_attribute(parse_dict, 'value')
            elif 'path' in parse_dict:
                split = parse_dict['path'].split('/')
                if split[0] == tag:
                    split.pop(0)
                    parse_dict['path'] = '/'.join(split)
                return OtherAttribute(tag, parse_dict['path'])
            # no path found, assume PV
            elif '/'.join(['/', tag, 'PV_D']) in module_info['attribute_paths']:
                return DiscreteAttribute(tag, attr_path='PV_D')
            elif '/'.join(['/', tag, 'PV']) in module_info['attribute_paths']:
                return IndicationAttribute(tag, attr_path='PV')
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
            print "PositionAttribute.tag:", tag
            if 'compare' in parse_dict:
                return self.generate_attribute(parse_dict, 'compare')
            else:
                # check if discrete module
                if '/'.join(['/', tag, 'PV_D']) in module_info['attribute_paths']:
                    if 'value' in parse_dict or parse_dict.value:
                        target_value = parse_dict.value[0]
                    elif '/'.join(['/', tag, 'OPEN']) in module_info['attribute_paths']:
                        value_dict = self.get_target_value(tag, ['OPEN', 'CLOSE'])
                        target_value = value_dict['/'.join([tag, parse_dict.action_word.upper()])]
                    else:
                        value_dict = {'start':1, 'stop':0}  #fixme - get namedsets from configuration. this is _MTR2_PV
                        target_value = value_dict[parse_dict.action_word]
                    return PositionAttribute(tag, attr_path='PV_D.CV', target_value=target_value)
                # otherwise return analog type
                else:
                    # fixme: taget_value should be obtained from from context of action word
                    if 'value' in parse_dict:
                        target_value = parse_dict.value[0]
                    else:
                        target_value = 0
                    return PositionAttribute(tag, attr_path='PV.CV', target_value=float(target_value))


        elif attribute_type in ['condition', 'compare']:
            tag, module_info = self.get_module_info(parse_dict.lhs)
            lhs = self.generate_attribute(parse_dict['lhs'], 'path')
            # Check for string type
            rhs = parse_dict.rhs
            opr = parse_dict['compare']

            if rhs.path or rhs.tag:
                rhs = self.generate_attribute(parse_dict['rhs'], 'path')
            elif rhs.value:
                rhs = rhs.value[0]
                if type(rhs) in [str, unicode] and not isNumber(rhs):
                    rhs = Constant(rhs.strip('\"'))
                    parse_dict['lhs'].value = parse_dict.rhs
                    lhs = self.generate_attribute(parse_dict['lhs'], 'path')
                elif isNumber(rhs):
                    if parse_dict.action_word in ['open', 'close']:
                        parse_dict.pop('compare')
                        parse_dict.tag = parse_dict.lhs.tag
                        parse_dict.value = parse_dict.rhs.value
                        lhs = self.generate_attribute(parse_dict, 'position')
                    rhs = Constant(float(rhs))
                else:  # path is based on lhs tag
                    parse_dict['rhs']['tag'] = tag
                    rhs = self.generate_attribute(parse_dict['rhs'], 'path')

            print "lhs:", type(lhs), "rhs:", type(rhs), "opr", opr
            return Compare(lhs, opr, rhs)

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
            if 'value' in parse_dict or parse_dict.value:

                val = parse_dict.value[0]

                self.logger.debug("Generating attribute from value: %s", val)

                if val in ['open', 'close']:
                    parse_dict.action_word = val
                    new_attr = self.generate_attribute(parse_dict, 'position')
                    value_dict = self.get_target_value(new_attr.tag, ['OPEN', 'CLOSE'])
                    if val == 'open':
                        new_attr.set_target_value(value_dict[new_attr.tag + '/' + 'OPEN'])
                    elif val == 'close':
                        new_attr.set_target_value(value_dict[new_attr.tag+'/'+'CLOSE'])
                    else:
                        self.logger.error("No target value found, cannot set in %s", new_attr)
                    return new_attr
                if val in ['AUTO', 'CAS', 'MAN', 'RCAS', 'ROUT', 'LO']:
                    tag, module_info = self.get_module_info(parse_dict)
                    print "ModeAttribute.tag: ", tag
                    return ModeAttribute(tag, target_mode=val)

                elif val in ['trip', 'reset']:
                    attr_class = command_vals[val]
                    self.logger.debug("Creating %s from: %s", attr_class.__name__, ' '.join(parse_dict.asList()))
                    return attr_class(parse_dict.tag, val)
                elif val in ['start', 'stop']:
                    parse_dict.action_word = val
                    return self.generate_attribute(parse_dict, 'position')
                    # self.logger.error("===>Need to implement motors for ", parse_dict.tag)
                    # return AttributeDummy()
                elif isNumber(val):
                    return Constant(float(val))
                elif parse_dict.tag == val:
                    attr_path = parse_dict.tag
                    tag = self.default_tag
                    return OtherAttribute(tag = tag, attr_path = attr_path)
                elif isString(val):
                    return Constant(val.string('\"'))


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

    def get_target_value(self, tag, path_list):
        '''Obtains the target value from DeltaV configuration, if possible. Will return Nonetype on error'''
        path_values = self.client.get_config_values(['/'.join([tag, attr_path]) for attr_path in path_list])['path_values']
        return dict(path_values)

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
