__author__ = 'vpeng'

# Just a Tool:
def finder('word'):
# need to be able to find str in the txt fiile and index which line it is
    with open("state_diagram.txt","r") as file:
        line_num = []
        for i,line in enumerate(file.read().split("\n")):
            if word in line:
                return line_num[i] = int('{}'.format(word,i+1))



diagram = open("state_diagram.txt","r") #not sure if it can pull out the .puml file directly or not
line_content = diagram.readlines() #type(lines) = 'List' so we can read the txt file from top to bottom

line_index = [l for l in range(0,len(line_content)-1)]



for item in line_index:
    #start reading: line_content[item]; use line_content[item].lstrip() to remove whitespace before the code
    #data mining?
    arrow = "-->"
    start = "[*]"
    colon = ":"
    if not arrows and not start and not colon in line_content[item]:
        # ignore unuseful lines
        continue

    else:
    # All arrows and colon can be indexed in each line, if any. Then use the index and 0, len(line) to represent "before" and "after". Is there better way to express before and after?


        def reader():
            if line_content[item].any(arrow) == True:
                pass #ParentState/SubState_before; SubState_after; Domain; Condition

                # Declare ParentState:  ParentState() = str after ("[*]" and "-->") and before (":")
                if line_content[item].any(colon) == True:
                    index_start = diagram.finder("[*] -->")
                    startline = line_content(line_num).lstrip()
                    ParentState = startline(9 : startline.index(":")-1)

                else:
                    index_start = diagram.finder("[*] -->")
                    startline = line_content(line_num).lstrip()
                    ParentState = startline(9 : len(startline)-1)


                # Declare Domain: Domain() = after ParentState + "-->" and before (:)
                index_Domain = diagram.finder(ParentState + "-->")
                for i in index_Domain:
                    Domainline = line_content(index_Domain).lstrip()
                    Domain = Domainline(Domainline.index("-->")+1 : Domainline.index(":")-1)


                # Declare SubStates:
                # SubState_before() = str before "-->" and not ParentState
                # SubState_after() = str after "-->" and not Domain
                if line_content[item].any(ParentState) == False or line_content[item].any(Domain) == False:
                    SubStateline = line_content[item].lstrip()
                    SubState_before = SubStateline(0 : SubStateline.index("-->")-1)

                    if line_content[item].any(colon) == True:
                        SubState_after = SubStateline(SubStateline.index("-->")+3 : SubStateline.index(":")-1)
                    else:
                        SubState_after = SubStateline(SubStateline.index("-->")+3 : len(SubStateline)-1)

                # Define Condition: str in lines that include "-->" and after ":" (TRUE or FALSE)
                def Condition():
                    pass


            elif line_content[item].any(arrow) == False and line_content[item].any(colon) == True:

                # Define CheckPoint: str in lines that not include "-->" anf after ":" (Comparison)
                # if CheckPoint == "test result" --> test complete and push str(Substate) to Test Bench
                def CheckPoint():
                    pass


# Another Alternative Tool
def Link(State1, State2):
    # if State1 and State2 both not empty, and can be found in the same line in file.
    # then print a string "State1 to State2" and it's line# from file.
    # if State2 is empty, and there is no "-->" after State1 in the line,
    # then print "State2 CheckPoint" and it's line# from file.

    # the UseCase of this function is that when coding Test Script,
    # we can call Link(State1,State2).Condition() and Link(State1,State2).CheckPoint()
    # to extract the test condition we need and put it into test bench.

    pass












