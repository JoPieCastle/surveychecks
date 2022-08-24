import re


class parser:
    def __init__(self, text=""):
        self.text = text
        self.varlist = ""
        self.parseVarInfo()

    def parseVarInfo(self):
        """Parses Text into a list of entries / a variable list

        Uses:
            self.text (string): information on variables, ranges and filter conditions

        Sets self.varlist:
            list: a list of rows, each element is a string containing information
            for one survey screen capturing everything between (Va: and Vb:)
        """
        # regex pattern for extraction of relevant info between (Va: and Vb:)
        regpatAll = re.compile(r"\(Va:(.*?)Vb:.*?\)", re.DOTALL)

        # find all variable relevant Information
        foundAll = regpatAll.findall(self.text)

        # keep only unique values by dic conversion and back to list
        varlist = list(dict.fromkeys(foundAll))

        # splitting each var regex by newline char
        outlist = []
        for var in varlist:
            outlist.append(var.split("\n"))

        # flattening list hirarchies
        outlist = sum(outlist, [])

        # keeping only entries with == (e.g. empty strings etc.)
        varlist = []
        for var in outlist:
            if re.search(r".*==.*", var) or re.search(r".*!=*", var):
                varlist.append(var)

        self.varlist = varlist

    def getVarInfo(self):
        return self.varlist

    def expandRanges(self, matchObj):
        """expands ranges of a variable seperated by ',' or '-' to a full pandas evaluation string seperated by OR |
        intended for use inside a re.sub function within inputToFullString()

        Args:
            matchObj (re.matchObj): match object from a regular expression

        Returns:
            string: expanded range string
        """
        # expand comma
        if matchObj.group(3) is not None and re.search(",", matchObj.group(3)):
            expandedList = []
            tempList = matchObj.group(3).split(",")
            for count, value in enumerate(tempList):
                expandedList.append(f"{matchObj.group(2)} == {tempList[count]}")
            return "(" + " | ".join(expandedList) + ")"

        # expand - ranges
        elif matchObj.group(3) is not None and re.search("[-]?[\d]+-[-]?[\d]+", matchObj.group(3)):
            expandedList = []
            parser = re.compile(r"([-]?[\d]*)-([-]?[\d]*)")
            subMatch = re.search(parser, matchObj.group(3))
            for i in range(int(subMatch.group(1)), int(subMatch.group(2)) + 1):
                expandedList.append(f"{matchObj.group(2)} == {i}")

            return "(" + " | ".join(expandedList) + ")"

        else:
            return matchObj.group(0)

    def addMissings(self, matchObj):
        """adds expanded missing values to the end of an expanded string if there is need for it

        Args:
            matchObj (re.matchObj): match object from regex

        Returns:
            string: with expanded missing values
        """
        if matchObj.group(2) is not None and re.search(",", matchObj.group(2)):
            expandedList = []
            tempList = matchObj.group(2).split(",")
            for count, value in enumerate(tempList):
                expandedList.append(f"{matchObj.group(1)} == {tempList[count]}")
            return "(" + " | ".join(expandedList) + ")"
        else:
            return f"{matchObj.group(1)} == {matchObj.group(2)}"

    def createVarNameList(self, evalStr):
        varlist = re.findall(r"[(&|;]+\s*[(&|;]*(.*?)\s[!=><]=\s", "|" + str(evalStr))  # filtering variables
        varlist = list(dict.fromkeys(varlist))  # removing duplicates

        return varlist

    def inputToFullString(self, inputString, out="expand"):
        """expands condition of a variable range string seperated by ',' or '-' to a full pandas evaluation string seperated by OR |
        by calling re.sub with expandedRanges() and addMissings()

        Args:
            inputString (string): string to be expanded
            out (string): whether to epand the string or give variable information

        Returns:
            string: expanded variable condition string or string with variable name
        """
        # regex pattern for var and value extraction
        regpat = re.compile(
            r"((\w*)\s[!=><]=\s([-]?[\d]*-(?=\,)[-]?[\d]*|([-]?[\d]*,?\s?)*))(\s\+\s(([-]?[\d]*,?\s?)*))?"
        )
        regpatMiss = re.compile(r"(\w*)\s[!=><]=.*\+\s(([-]?[\d]*,?\s?)*)")
        if out == "expand":
            strOut = re.sub(regpat, self.expandRanges, inputString)
            if re.match(regpatMiss, inputString):
                if re.search(regpatMiss, inputString).group(2) != "":
                    strOut = re.sub(r"\+(([-]?[\d]*,?\s?)*)", "", strOut)
                    return strOut + " | " + re.sub(regpatMiss, self.addMissings, inputString)
            else:
                return strOut

        elif out == "variable":
            try:
                return regpat.findall(inputString)[0][1]
            except:
                raise Exception(f'Problem parsing the following variable string: "{inputString}"')
        else:
            raise Exception('not an allowed "out" option, only "expand" and "variable" allowed')

    def singleExpParse(self, expression, out="value"):
        """gives either the value or the varname of a conditions, such as 'varName == range'

        Args:
            expression (string): The condition.
            out (str, optional): Whether to output variable name or value. Defaults to 'value'.

        Returns:
            string: with either value or variable
        """
        regpat = re.compile(r"(.*)[=!><]=(.*)")

        if out == "value":
            return re.search(regpat, expression).group(2).replace(" ", "")
        elif out == "variable":
            return re.search(regpat, expression).group(1).replace(" ", "")
        else:
            raise Exception('not an allowed "out" option, only "value" and "variable" allowed')

    def logicSplit(self, evalString):

        # splitting on &
        logicSplitList = evalString.split("&")

        for num, value in enumerate(logicSplitList):
            # adding & to the eval string again at the beginning
            if len(logicSplitList) - 1 == num:
                pass
            else:
                logicSplitList[num + 1] = f"& {logicSplitList[num+1]}"

        # splitting on |
        for num, value in enumerate(logicSplitList):
            if "|" in value:
                secondSplit = value.split("|")

                for numerodos, valuedos in enumerate(secondSplit):
                    # appending |
                    if len(secondSplit) - 1 == numerodos:
                        pass
                    else:
                        secondSplit[numerodos + 1] = f"| {secondSplit[numerodos+1]}"

                logicSplitList[num] = secondSplit

        # flattening hirarchies
        flattenList = (
            lambda irregular_list: [element for item in irregular_list for element in flattenList(item)]
            if type(irregular_list) is list
            else [irregular_list]
        )

        outList = []
        for value in flattenList(logicSplitList):
            if len(value) == 0:
                pass
            else:
                outList.append(value)

        return outList

    def filterEvalExtender(self, evalString, filterDic):
        # using the recusive filter extention function
        out = self.recursiveEvalExtender(evalString, filterDic)

        # flattening list hirarchies of output
        flattenList = (
            lambda irregular_list: [element for item in irregular_list for element in flattenList(item)]
            if type(irregular_list) is list
            else [irregular_list]
        )

        # cleaning up the string
        out = " ".join(flattenList(out))
        out = re.sub(r"\(\&", r"&(", out)
        out = re.sub(r"\(\|", r"|(", out)

        return out

    def recursiveEvalExtender(self, evalString, filterDic):
        """Recursive function"""
        indexCounter = 0
        # parse string into single expressions seperated by | and &
        splitList = self.logicSplit(evalString)

        for index, value in enumerate(splitList):
            try:
                # get varname
                varname = self.createVarNameList(value)[0]

                # check if varname has a filtercondition
                for key, dicValue in filterDic.items():
                    if varname == key:
                        # append value as a list after the index where the match was found
                        indexCounter += 1  # keepting track of how many additions where made
                        splitList[index] = f"({value}"

                        # look if there are any other | or & in string
                        if "|" in dicValue or "&" in dicValue:
                            splitList[index] = f"({value}"
                            # TODO explain
                            splitList.insert(
                                index + indexCounter,
                                self.recursiveEvalExtender(f"& {dicValue})", filterDic),
                            )
                        else:
                            splitList.insert(index + indexCounter, f"& {dicValue})")
            except:
                raise Exception(f"problem at parsing {splitList} and {value}")
        return splitList


if __name__ == "__main__":

    filtTest = {}
    filtTest[
        "SD29A_1"
    ] = "(SD28 >= 1 & (SD27 == 2 & (SD26 == 1 | SD26 == 2 | SD26 == 3 | SD26 == 4))) | ((SD27 == 1 & (SD26 == 1 | SD26 == 2 | SD26 == 3 | SD26 == 4)) | (SD27 == 2 & (SD26 == 1 | SD26 == 2 | SD26 == 3 | SD26 == 4)))"

    filtTest = {
        "SD28": "SD27 == 2",
        "SD29A_1": "SD28 >= 1 | (SD27 == 1 | SD27 ==  2)",
        "SD33_1": 'SD29A_1 != "nan"',
        "SD38": "SD35 == 1",
        "SD46": "SD38 == 1 | SD33_1 == 1",
    }

    pars = parser()
    evalString = "SD38 == 1 | SD33_1 == 1"

    shouldEvaluateTo = (
        '(SD38 == 1 & (SD35 == 1)) | (SD33_1 & ((SD29A_1 != "nan") & (SD28 >= 1 | (SD27 == 1 | SD27 ==  2))'
    )

    # print(pars.logicSplit('& SD7_10 == 1'))

    def extender(evalString, pars, filtTest):
        """Recursive function"""
        indexCounter = 0
        # parse string into | and
        splitList = pars.logicSplit(evalString)

        print(splitList)

        for index, value in enumerate(splitList):
            # get varname
            varname = pars.createVarNameList(value)[0]
            print(varname)

            # check if varname has a filtercondition
            for key, dicValue in filtTest.items():
                if varname == key:
                    print("yes")
                    # append value as a list after the index where the match was found
                    indexCounter += 1  # keepting track of how many additions where made
                    splitList[index] = f"({value}"

                    # look if there are any other | or & in string
                    if "|" in dicValue or "&" in dicValue:
                        # indexCounter += 1
                        splitList.insert(
                            index + indexCounter,
                            extender(f"& {dicValue})", pars, filtTest),
                        )
                    else:
                        splitList.insert(index + indexCounter, f"& {dicValue})")

        return splitList

    def extender2(evalString, pars, filtTest, indexCounter=0):
        # parse string into | and
        splitList = pars.logicSplit(evalString)
        splitListCopy = splitList.copy()
        newlevel = False
        # loop through the vars of the filtercondition
        for index, value in enumerate(splitListCopy):
            # get varname to compare to filterDic
            varname = pars.createVarNameList(value)[0]

            # check if varname has a filtercondition
            for key, dicValue in filtTest.items():
                # if there is a filtercondition, append it
                if varname == key:
                    indexCounter += 1
                    splitList.insert(index + indexCounter, f"& {dicValue})")
                    newlevel = [index, True]

        return [splitList, newlevel]

    out = extender(evalString, pars, filtTest)
    print(out)
    import pprint

    flattenList = (
        lambda irregular_list: [element for item in irregular_list for element in flattenList(item)]
        if type(irregular_list) is list
        else [irregular_list]
    )

    out = " ".join(flattenList(out))
    out = re.sub(r"\(\&", r"&(", out)
    out = re.sub(r"\(\|", r"|(", out)

    print("\n", out)

    """
    evalStr = 'SD5 == 7'

    pars = parser()

    out = pars.inputToFullString(evalStr, out = 'variable') 
    print(out)
    
    varlist = re.findall(r'[(&|;]+\s*[(&|;]*(.*?)\s[!=><]=\s', '|'+str(evalStr)) #filtering variables
    varlist = list(dict.fromkeys(varlist)) #removing duplicates
    print(varlist)
    """
