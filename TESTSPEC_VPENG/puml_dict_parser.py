__author__ = 'vpeng'

#TODO: execute plantUML_state_lexer.py

class Tool(object):
    def __init__(self,filename):
        self.getfile = open(filename, mode = "r")
        self.line_content = self.getfile.readlines()
        self.line_index = [l for l in range(0,len(self.line_content)-1)]
        self.search_result = []

    def search(self,word):
        #To find str in the file and index the line number
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


class GetDict(Tool):
    def __init__(self,filename):
        Tool.__init__(self,filename)


    def state_action(self):
        '''State:Action Dictionary'''
        action_index = Tool.search(self, word = 'Token.StateAttr')

        for item in action_index:
            self.Action = Tool.gettoken(self, index = item) # StateAttr List
            self.State = Tool.gettoken(self,index = item-1) # State List

        return dict(zip((self.State,), (self.Action,)))

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

        self.SouceDest = zip((self.TranSource,),(self.TranDest,))

        return dict(zip((self.Transition,),(self.SouceDest,)))

    def source_destination(self):
        '''SourceState:DestState Dictionary'''
        destination_index = Tool.search(self,word = 'Token.DestState')

        for item in destination_index:
            self.DestState = Tool.gettoken(self,index = item) # DestState List
            self.SourceState = Tool.gettoken(self,index = item - 1) # SourceState List

        return dict(zip((self.SourceState,), (self.DestState,)))

    def superstate(self):
        ''' SuperState List'''
        #TODO: Verify that SuperState DO NOT have a StateAttr from latest lexer output, or improve this definition.
        allstates_index = Tool.search(self,word = 'Token.State')

        for item in allstates_index:
            if 'Token.StateAttr' not in self.line_content[item+1]:
                self.SuperState = Tool.gettoken(self,index = item) #SuperState List

        return self.SuperState


