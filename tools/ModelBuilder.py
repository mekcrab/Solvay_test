'''Module contains definitions for model builder class.

A model builder's primary function is to generate python objects from a stream of token:value
pairs. These pairs will generally be the product of a pygments lexer.

'''

__author__ = 'erik'

import pygments.token as Token

import StateModel
from plantUML_state_lexer import STATE, SALIAS, SATTR, SSTART, SEND, TSOURCE, TDEST, TATTR

class ModelBuilder(object):

    # Text and Error tokens ignored by default
    token_dict = {
        Token.Text: lambda x: None,
        Token.Error: lambda x: None,
    }

    def __init__(self, model_class, *args, **kwargs):
        self.model_class = model_class
        self.model = self.model_class()

    def parse(self, token_stream):
        '''Override parsing method in subclass'''
        for token in token_stream:
            # if token not part of actionable items, merely add it to the queue
            # otherwise take action on first actionable item in queue

            pass


class StateModelBuilder(ModelBuilder):
    '''
    Generates State Models from a token stream.
    '''

    def __init__(self, *args, **kwargs):
        ModelBuilder.__init__(StateModel.StateDiagram)

    def parse(self, input_stream):
        '''
        :param: input_stream - an input stream of (token, value) pairs.
        :return: StateModel.StateDiagram populated with state/transition hierarchy
        '''
        pass

    def assign_state(self, q):
        '''All state names are unique and required for assignment'''


    def lookup_state(self, q):
        pass

    def add_state_attr(self, q):
        pass

    def start_superstate(self, q):
        pass

    def end_superstate(self, q):
        pass

    def assign_trans_source(self, q):
        pass

    def assign_trans_dest(self, q):
        pass

    def add_trans_attr(self, q):
        pass

    '''dictionary mapping tokens to assignment functions
    --> updates from base class dictionary'''
    token_dict = ModelBuilder.token_dict.update({
        STATE: assign_state,
        SALIAS: lookup_state,
        SATTR:  add_state_attr,
        SSTART: start_superstate,
        SEND: end_superstate,

        TSOURCE: assign_trans_source,
        TDEST:  assign_trans_dest,
        TATTR: add_trans_attr,
    })

