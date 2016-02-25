__author__ = 'vpeng'

# Execute PlantUML_Lexer.py
#import os
#os.system('../../TESTSPEC_EKOPACHE/tools/PlantUML_Lexer.py')

# filename = output of plantUML_state_lexer
#filename = 'fake_PH_AL_SMPL_CVAS_test_out.txt'
#file = open(filename, mode="r")

class Tool(object):
    def __init__(self):
        self.getfile = file
        self.line_content = self.getfile.readlines()
        self.line_index = [l for l in range(0,len(self.line_content))]
        self.search_result = []

    def search(self, word):
        #Find str in the file and index the line number
        enfile = enumerate(self.getfile.read().split("\n"))
        line_by_content = dict(list(enfile))
        content_by_line = dict(zip((line_by_content.values(),), (line_by_content.keys(),)))
        for i in range(0, len(self.line_content)):
            if word in self.line_content[i]:
                self.search_result.append(content_by_line[i])
                return self.search_result
            else:
                raise TypeError

    def gettoken(self, index):
        string = self.line_content[index]
        splitted = string.split() #Split Alias (0) and its token (1)
        return splitted[1] #Return token

    def dictlist(self, keyword, value):
        '''To avoid keyword replacement in dictionary, we must use dictionary list '''
        z = zip((keyword,), (value,))
        dictlist = []
        for n in range(0, len(value)):
            dictlist.append(dict([z[n]]))
        return dictlist

    def wrapdict(self,DL):
        '''
        Wrap up values to the same keyword on dictionary
        i.e: >>>GetDict.source_destination
        --> {sourceA : [destA1, destA2, destA3] , sourceB: [destB1,destB2]}
        '''

        new_dict = {}
        for x in DL:
            for y in x:
                if y in new_dict:
                    new_dict[y].append(x[y])
                    new_dict[y].sort()
                else:
                    new_dict[y] = [x[y]]
        return new_dict

class GetList(Tool):
    def __init__(self):
        Tool.__init__(self)

    def Action(self):
        action_index = Tool.search(self, word = 'Token.StateAttr')
        self.Action = []
        self.AState = []
        for item in action_index:
            self.Action.append(Tool.gettoken(self, index = item)) # StateAttr List
            self.AState.append(Tool.gettoken(self, index = item -1)) #Action List

        return self.Action

    def AState(self):

        return self.AState

    def Transition(self):
        transition_index = Tool.search(self, word = 'Token.TranAttr')

        self.Transition = []
        self.TranSource = []
        self.TranDest = []

        for item in transition_index:

            self.Transition.append(Tool.gettoken(self, index = item)) # TranAttr List
            self.TranSource.append(Tool.gettoken(self, index = item - 2)) # SourceState List
            self.TranDest.append(Tool.gettoken(self,index = item - 1)) # DestState List

        return self.Transition

    def TranSource(self):

        return self.TranSource

    def TranDest(self):

        return self.TranDest

    def DestState(self):
        destination_index = Tool.search(self, word = 'Token.DestState')
        self.DestState = []
        self.SourceState = []

        for item in destination_index:
            self.DestState.append(Tool.gettoken(self, index = item)) # DestState List
            self.SourceState.append(Tool.gettoken(self, index = item - 1)) # SourceState List

        return self.DestState

    def AllStates(self):
        return set(self.SourceState + self.DestState) # All States List discarding duplicates

    def SourceState(self):

        return self.SourceState

    def SuperState(self):

        pass


class GetDict(GetList):
    def __init__(self):
        GetList.__init__(self)


    def state_action(self):
        '''
        State:Action Dictionary.
        One State can contain multiple Actions in a List
        '''
        dictlist = Tool.dictlist(self, keyword = self.AState, value = self.Action)

        return Tool.wrapdict(self, DL = dictlist)

    def transition_states(self):
        '''Transition:States Dictionary.
        This Dictionary is able to index the Source and Destination of an identified transition
        States include (TranSource, TranDest)
        Same Transition may contain multiple (TranSource, TranDest) in a List
        '''

        self.TranSourceDest = zip((self.TranSource,), (self.TranDest,))
        dictlist = Tool.dictlist(self, keyword = self.Transition, value = self.TranSourceDest)

        return Tool.wrapdict(self, DL = dictlist)

    def states_transition(self):
        '''(TranSource, TranDest):Transition Dictionary'''
        dictlist = Tool.dictlist(self, keyword = self.TranSourceDest, value = self.Transition)

        return Tool.wrapdict(self, DL = dictlist)

    def source_transition(self):
        '''SourceState:Transition Dictionary.
        One SourceState can have multiple Transitions in a List
        '''
        dictlist = Tool.dictlist(self, keyword = self.TranSource, value = self.Transition)
        return Tool.wrapdict(self, DL = dictlist)

    def source_destination(self):
        '''
        SourceState:DestState Dictionary
        One Source can have multiple Destination in a List
        '''

        dictlist = Tool.dictlist(self, keyword = self.SourceState, value = self.DestState)

        return Tool.wrapdict(self, DL = dictlist)

    def superstate_childstart(self):
        '''
        SuperState:ChildStart Dictionary
        Childstart is the Start State inside the SuperState
        '''

        pass

    def superstate_child(self):
        '''SuperState:ChildState Dictionary
        ChildState is a List that contains all States inside the superstate
        '''

        pass


#file.close()


if __name__ == "__main__":
    from tools.PlantUML_Lexer import puml_state_lexer
    from pygments import lex
    from pprint import pprint as pp

    test_file = 'PH_AL_CLN_STM.puml'

    # opens test file for reading
    with open(test_file) as ftest:
        # saves text from file as python string
        test_text = ftest.read().encode('utf-8')

    # generator of (token, value) tuples
    tkns = lex(test_text, puml_state_lexer())

    # list of token_type, value pairs
    list_out = [(x[0],x[1]) for x in tkns]

    # get a string printout of this list:
    str_out = pp(list_out)


    print "..."

