__author__ = 'vpeng'

#TODO: import plantUML_state_lexer.py

puml = open("../../TESTSPEC_EKOPACHE/tools/test_out.html", mode = "r")

line_content = puml.readlines()
line_index = [l for l in range(0,len(line_content)-1)]

#TODO: Install library to create spreadsheet files: https://github.com/python-excel
import xlwt

headers = [
    'SuperState', #C0
    'SourceState', #C1
    'DestState', #C2
    'TransAttr', #C3
    'State', #C4
    'StateAttr' #C5
]

workbook = xlwt.Workbook(encoding = "utf-8")
sheet1 = workbook.add_sheet("Sheet1")

for h in range(0,len(headers)-1):
    sheet1.write(h,0,headers[h])
    continue

r = 0
for n in line_index:
    string = line_content[n]
    splitted = string.split()
    if 'Token.SourceState' in splitted:
        r = r + 1
        sheet1.write(1,r,splitted[1]) # fill SourceState Cell
        if 'Token.DestState' in line_content[n+1]:
            # fill DestState
            DestString = line_content[n+1]
            DestSplitted = DestString.split()
            sheet1.write(2,r,DestSplitted[1])
            if 'Token.TransAttr' in line_content[n+2]:
                # fill TransAttr
                TranString = line_content[n+2]
                TranSplitted = TranString.split()
                sheet1.write(3,r,TranSplitted[1])

    if 'Token.State' in splitted:
        r = r + 1
        if 'Token.StateAttr' in line_content[n+1]:
            sheet1.write(4,r,splitted[1]) # fill State Cell
            StateAttrString = line_content[n+1]
            StateAttrSplitted = StateAttrString.split()
            sheet1.write(5,r,StateAttrSplitted[1]) # fill StateAttr Cell
        if 'found' in line_content[n+1]:
            sheet1.write(0,r,splitted[1]) # fill SuperState Cell

continue

#TODO: filename generator
Workbook.save('filename.xls');
