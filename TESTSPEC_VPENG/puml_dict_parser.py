__author__ = 'vpeng'

#TODO: execute plantUML_state_lexer.py

class tool(object):
    def __init__(self,filename,*args):
        self.getfile = open(filename, mode = "r")
        if args:
            self.word = args

        self.enfile =  enumerate(self.getfile.read().split("\n"))
        self.line_by_content = dict(list(self.enfile))
        self.content_by_line = dict(zip(self.line_by_content.values(), self.line_by_content.keys()))

    def get_content(self):
        self.line_content = self.getfile.readlines()
        self.line_index = [l for l in range(0,len(self.line_content)-1)]

        for n in self.line_index:
            self.string = self.line_content[n]
            self.splitted = self.string.split()
            return self.splitted

        return self.line_content

    def search(self):
        #To find str in the file and index the line number
        self.result = []
        for i in range(0,len(self.line_content)-1):
            if self.word in self.line_content[i]:
                self.result.append(self.content_by_line[i])
                return self.result
            else:
                raise TypeError


class get_map(tool):
    def __init__(self,filename,*args):
        self.State = state
        self.SAttr = SAttr
        tool.__init__(self,filename,args)

    def state_action(self,state,action):
        self.SAttr_index = search()


