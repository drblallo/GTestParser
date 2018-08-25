import re
from vim import *
from os.path import expanduser

knowLileRegex = r"^\s*#(\d+)\s+(.+)\s+([^\s\(\)]+)\s*$"
unkownLileRegex = r"^\s*#(\d+)\s+(.+)\s+\((\S+)\)\s*$"
functionNameRegex = r"^\s*0x[\d\w]+\s+(.+)\s*$"

class StackLine:

    def __init__(self, sourceFile, function, line, known):
        self.sourceFile = sourceFile.replace(vim.eval("getcwd()"), ".")
        self.sourceFile = self.sourceFile.replace(expanduser("~"), "~")
        self.function = function
        self.simplifyFunctionName()
        self.line = line
        self.known = known

    def simplifyFunctionName(self):
        self.function = re.match(functionNameRegex, self.function).group(1)
    
    def write(self):
        if self.function != "":
            return "\t+" + self.function + "\n\t\t" + self.sourceFile 
        else:
            return "\t-" + self.sourceFile
    def asVector(self):
        vec = []

        if self.known == True:
            vec.append("+\t" + self.sourceFile)
        else:
            vec.append("-\t" + self.sourceFile)
        vec.append("\t=> " + self.function)
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
            if len(reg.stackTrace) != 0:
                for line in reg.asVector():
                    self.buffer.append(line)
                self.buffer.append("")
                self.buffer.append("")

    def compleatedRegistry(self):
        self.regitries.append(self.currentRegistry)
        self.currentRegistry = LeakRegistry()

    def parseUnkowLine(self, parseUnkowLine):
        divided = re.match(unkownLileRegex, parseUnkowLine)
        val = StackLine(divided.group(3), divided.group(2), divided.group(1), False)
        self.currentRegistry.stackTrace.append(val)

    def createReport(self):
        report = ""
        
        for line in self.extraStuff:
            report = report + line
        
        report = report +"-----\n" 

        for reg in self.regitries:
            if len(reg.stackTrace) != 0:
                report = report + reg.write() + "\n"
        return report

    def parseKnownLine(self, line):
        divided = re.match(knowLileRegex, line) 
        stackTraceCount = divided.group(1)
        functionName = divided.group(2)
        file = divided.group(3)
        val = StackLine(file, functionName, stackTraceCount, True)
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

        if re.match(r"SUMMARY: \.*", line) :
            self.ended = True
            return
        
        if re.match(r"==\.*", line)or re.match(r"^\-+\s*$", line):
            return

        if re.match(knowLileRegex, line):
            self.parseKnownLine(line)
            return

        if re.match(unkownLileRegex, line):
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
