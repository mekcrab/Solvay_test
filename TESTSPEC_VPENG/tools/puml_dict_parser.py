__author__ = 'vpeng'

import TESTSPEC_EKOPACHE.tools.plantUML_state_lexer

#TODO: filename = output of plantUML_state_lexer

class Tool(object):
    def __init__(self,filename):
        self.getfile = open(filename, mode = "r")
        self.line_content = self.getfile.readlines()
        self.line_index = [l for l in range(0,len(self.line_content)-1)]
        self.search_result = []

    def search(self,word):
        #Find str in the file and index the line number
        enfile = enumerate(self.getfile.read().split("\n"))
        line_by_content = dict(list(enfile))
        content_by_line = dict(zip((line_by_content.values(),), (line_by_content.keys(),)))
        for i in range(0,len(self.line_content)-1):
            if word in self.line_content[i]:
                self.search_result.append(content_by_line[i])
                return self.search_result
            else:
                raise TypeError

    def gettoken(self,index):
        string = self.line_content[index]
        splitted = string.split() #Split Alias and its token
        return splitted[1] #Return token

    def dictlist(self,keyword,value):
        '''To avoid keyword replacement in dictionary, we must use dictionary list '''
        z = zip(keyword,value)
        dictlist = []
        for n in range(0,len(value)):
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


class GetDict(Tool):
    def __init__(self,filename):
        Tool.__init__(self,filename)


    def state_action(self):
        '''
        State:Action Dictionary.
        One State can contain multiple Actions in a List
        '''
        action_index = Tool.search(self, word = 'Token.StateAttr')

        for item in action_index:
            self.Action = Tool.gettoken(self, index = item) # StateAttr List
            self.State = Tool.gettoken(self,index = item-1) # State List

        dictlist = Tool.dictlist(self, keyword = self.State, value = self.Action)

        return Tool.wrapdict(self,DL = dictlist)

    def transition_states(self):
        '''Transition:States Dictionary.
        This Dictionary is able to index the Source and Destination of an identified transition
        States include (TranSource, TranDest)
        '''
        transition_index = Tool.search(self, word = 'Token.TranAttr')

        for item in transition_index:

            self.Transition = Tool.gettoken(self,index = item) # TranAttr List
            self.TranSource = Tool.gettoken(self, index = item - 2) # SourceState List
            self.TranDest = Tool.gettoken(self,index = item - 1) # DestState List

        self.SourceDest = zip((self.TranSource,),(self.TranDest,))
        dictlist = Tool.dictlist(self, keyword = self.Transition, value = self.SourceDest)

        return Tool.wrapdict(self,DL = dictlist)

    def source_transition(self):
        '''SourceState:Transition Dictionary.
        Onr SourceState can have multiple Transitions in a List
        '''
        dictlist = Tool.dictlist(self, keyword = self.TranSource, value = self.Transition)
        return Tool.wrapdict(self, DL = dictlist)

    def source_destination(self):
        '''
        SourceState:DestState Dictionary
        One Source can have multiple Destination in a List
        '''
        destination_index = Tool.search(self,word = 'Token.DestState')

        for item in destination_index:
            self.DestState = Tool.gettoken(self,index = item) # DestState List
            self.SourceState = Tool.gettoken(self,index = item - 1) # SourceState List

        dictlist = Tool.dictlist(self, keyword = self.SourceState, value = self.DestState)

        return Tool.wrapdict(self, DL = dictlist)

    def superstate(self):
        ''' SuperState List'''
        pass


