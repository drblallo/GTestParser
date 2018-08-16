import re
from vim import *
from os.path import expanduser


class StackLine:

    def __init__(self, sourceFile, function, line):
        self.sourceFile = sourceFile.replace(vim.eval("getcwd()"), ".")
        self.sourceFile = self.sourceFile.replace(expanduser("~"), "~")
        self.function = function
        self.line = line

    def write(self):
        if self.function != "":
            return "\t+" + self.function + "\n\t\t" + self.sourceFile 
        else:
            return "\t-" + self.sourceFile
    def asVector(self):
        vec = []

        if self.function != "":
            vec.append("+\t" + self.sourceFile)
            vec.append("\t=> " + self.function)
        else:
            vec.append("-\t" + self.sourceFile)
            vec.append("\t=> ??????????")
        return vec


class LeakRegistry:

    def __init__(self):
        self.stackTrace = []
        self.description = "NO DESC"

    def asVector(self):
        vec = []
        vec.append(self.description)
        for line in self.stackTrace:
            for l in line.asVector():
                vec.append(l)
        return vec

    def write(self):
        string = self.description
        for line in self.stackTrace:
            string = string + line.write() + "\n"
        return string;


class AsanParser:
    """asan parser"""
    def __init__(self, buffer):
        self.regitries = []
        self.buffer = buffer
        self.started = False
        self.currentRegistry = LeakRegistry()
        self.ended = False
        self.extraStuff = []
        self.neverCalled = True
        
    def parse(self):
        for line in self.buffer:
            self.parseLine(line)
        
    def write(self):
        if not self.started:
            return
        del vim.current.buffer[0:len(vim.current.buffer)]
        
        for line in self.extraStuff:
            self.buffer.append(line)
        
        self.buffer.append("----found: " + str(len(self.regitries)))
        self.buffer.append("")

        for reg in self.regitries:
            if reg.description != "NO DESC":
                for line in reg.asVector():
                    self.buffer.append(line)
                self.buffer.append("")
                self.buffer.append("")

    def compleatedRegistry(self):
        self.regitries.append(self.currentRegistry)
        self.currentRegistry = LeakRegistry()

    def parseUnkowLine(self, parseUnkowLine):
        divided = re.match(r"\s*#(\d+)\s+(\w+)\s+(in\s+.+\s+)?\((\S+)\+\w+\)\s*", parseUnkowLine)
        val = StackLine(divided.group(divided.lastindex), "", divided.group(1))
        self.currentRegistry.stackTrace.append(val)

    def createReport(self):
        report = ""
        
        for line in self.extraStuff:
            report = report + line
        
        report = report +"-----\n" 

        for reg in self.regitries:
            if reg.description != "NO DESC":
                report = report + reg.write() + "\n"
        return report

    def parseKnownLine(self, line):
        divided = re.match(r"\s*#(\d+)\s(\w+)\s+in\s+(.+)\s+([^\s:]+:\d+)(:\d+)?\s*", line) 
        stackTraceCount = divided.group(1)
        pointer = divided.group(2)
        functionName = divided.group(3)
        file = divided.group(4)
        val = StackLine(file, functionName, stackTraceCount)
        self.currentRegistry.stackTrace.append(val)

    def parseLine(self, line):
        if self.ended == True:
            self.extraStuff.append(line)
            return

        if re.match(r"=+\s*", line):
            self.started = True
            return

        if not self.started:
            self.extraStuff.append(line)
            return

        if re.match(r"SUMMARY: \.*", line):
            self.ended = True
            return
        
        if re.match(r"==\.*", line):
            return

        if re.match(r"\s*#\d+\s\w+\s+in\s+.+\s+[^\s:]+:\d+(:\d+)?\s*", line):
            self.parseKnownLine(line)
            return

        if re.match(r"\s*#\d+\s+\w+\s+(in\s+.+\s+)?\(\S+\+\w+\)\s*", line):
            self.parseUnkowLine(line)
            return

        if line.isspace() or line == "" or line == "\n": 
            self.compleatedRegistry();
            self.neverCalled = False
            return

        if self.currentRegistry.description != "NO DESC":
            self.extraStuff.append(self.currentRegistry.description)
        self.currentRegistry.description = line
        
def parseFile(path):
    parser = AsanParser(None)
    file = open(path, "r")
    for line in file.readlines():
        parser.parseLine(line)
     
    print(parser.createReport())

def parseBuffer():
   parser = AsanParser(vim.current.buffer)
   parser.parse()
   parser.write()
