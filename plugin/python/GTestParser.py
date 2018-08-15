import re
from vim import *

table = {}
startedParsing = False
finishedParsing = False
lines = []
isSuspdended = False


def addToTable(line, passed):
    global lines
    removedStatus = (re.sub(r"\[\s*\w*\s*\]\s*", "", line))
    removedStatus = removedStatus.replace(".", " ")
    names = removedStatus.split(" ")

    group = names[0]
    name = names[1]
    if not group in table:
        table[group] = {}

    table[group][name] = (passed, lines[:])

    lines = []

def fixedLine(line):
    return line

def parseLine(line):
    global startedParsing
    global finishedParsing
    global isSuspdended

    if (finishedParsing):
        return

    if re.match(r"\[\s*OK\s*\]\s*[\d|\w]+\.[\d|\w]+\s*.*", line):
        addToTable(line, True)
        return

    if re.match(r"\[\s*FAILED\s*\]\s*[\d|\w]+\.[\d|\w]+\s*.*", line):
        addToTable(line, False)
        return

    if re.match(r"\[=+\]\.*", line):
        if (startedParsing):
            finishedParsing = True
        startedParsing = True
        return

    if re.match(r"\[-+\]\.*", line):
        isSuspdended = not isSuspdended
        return

    if startedParsing and not re.match(r"\[.*\]\.*", line) and not line.isspace() and not isSuspdended:
        lines.append(fixedLine(line))

def failSuccessName(val):
    if val == True:
        return "OK"
    else:
        return "KO"

def write(string, out):
    if out == None:
        print(string)
    else:
        out.append(string)


def writeTestResult(testName, success, extraLines, buffer):
    write("\t" + failSuccessName(success) + " " + testName, buffer)
    for line in extraLines:
        write("\t\t" + line, buffer)


def printTable(onlyPrintFailure, buffer):
    for group, val in table.items():
        allSucceded = True
        for test, val2 in val.items():
            if val2[0] == False:
                allSucceded = False

        if not allSucceded:
            write(failSuccessName(allSucceded) + " " + group, buffer)

        for test, val2 in val.items():
            if not val2[0]:
                writeTestResult(test, val2[0], val2[1], buffer)

    if onlyPrintFailure == True:
        return

    write("------", buffer)
    for group, val in table.items():
        allSucceded = True
        for test, val2 in val.items():
            if val2[0] == False:
                allSucceded = False

        write(failSuccessName(allSucceded) + " " + group, buffer)

        for test, val2 in val.items():
            if val2[0]:
                writeTestResult(test, val2[0], val2[1], buffer)

def findTestDeclaration():
    buffer = vim.current.buffer
    index = 0
    for num in range(0, len(buffer)):
        if vim.current.line == buffer[num]:
            index = num
            break


    return buffer[index]
    while index > 0:
        if re.match("TEST(_F)?\s*\(.*,.*\)", buffer[index]):
            return buffer[index]
        index = index - 1

    return None

def getCurrentTestName():
    s = findTestDeclaration()
    
    s = s[s.find("("):s.find(")")]
    s = s.split(",")

    vim.command("let s:local = '%s'"% s[0])

def runOnBuffer():
    global startedParsing
    global finishedParsing

    finishedParsing = False
    startedParsing = False
    table.clear()
    for line in vim.current.buffer:
        parseLine(line)
    del vim.current.buffer[0:len(vim.current.buffer)]
    printTable(False, vim.current.buffer)
