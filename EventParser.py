import os
import re
import json
import subprocess
import sys
import logging

logger = logging.getLogger(__name__)
class eventParser:
    #Used if checking event logs on the machine the activegate is installed on
    def createOutputLocal():
        #Command line args documentation https://www.petri.com/command-line-event-log
            #This command will only check the 100 most recent event logs. Change or remove the /c:{#} to increase or decrease this threshold
        myCmd = 'powershell.exe wevtutil qe Microsoft-Windows-PrintService/Operational /rd:true /f:text'

        #Executes the command and puts the text return into the output variable
        output = os.popen(myCmd).read()

        #Turns the output into a list
        outputList = output.splitlines()

        #Local variables that hold all information from log output
        #!IMPORTANT! If you want to use a different event change the listNames, the if startswith statements, the list name infron to of the append function, and the text inside the Regex
        eventNum = []
        logName = []
        logSource = []
        date = []
        eventId = []
        task = []
        level = []
        opcode = []
        computer = []
        description = []
        bytesize = []
        value = []

        event = 0
        #For loop that breaks apart the command line return and uses regex to remove and white spaces as and the value in front of the actual data.
            #List name above should be the same whatever is being regexed out of the line
        event = 0
        for index, line in enumerate(outputList):
            if line.startswith('Event'):
                eventNum.append(event)
                event = event + 1
            elif line.startswith('  Log Name:'):
                logName.append(re.sub(r"(.*)\ Log Name: ","",line))
            elif line.startswith('  Source:'):
                logSource.append(re.sub(r"(.*)\ Source: ","",line))
            elif line.startswith('  Date:'):
                date.append(re.sub(r"(.*)\Date: ","",line))
            elif line.startswith('  Event ID:'):
                eventId.append(re.sub(r"(.*)\ Event ID: ","",line))
            elif line.startswith('  Task:'):
                task.append(re.sub(r"(.*)\ Task: ","",line))
            elif line.startswith('  Level:'):
                level.append(re.sub(r"(.*)\ Level: ","",line))
            elif line.startswith('  Opcode:'):
                opcode.append(re.sub(r"(.*)\ Opcode: ","",line))
            elif line.startswith('  Computer:'):
                computer.append(re.sub(r"(.*)\ Computer: ","",line))
            elif line.startswith('  Description:'):
                description.append(outputList[index+1])

        #Extracts a certain value from a part of the log description in this case we are extracting the bytes amount from the description of a log
        for index, type in enumerate(task):
            if type == 'Printing a document':
                bytesize.append(re.search(r"Size in bytes: (.*?)\.", description[index]).group(1))
                value.append(index)
        #Converts byte value from string to int all data pulled from command are string if you want it in a different format you will have to convert it.
        byteAsNumber = list(map(int, bytesize))

        #returns all data extracted from the log
        return eventNum, logName, logSource, date, eventId, task, level, opcode, computer, description, byteAsNumber, value

    #Create output for a remote machine !IMPORTANT! If remote machine is not in the same domain in the activegate additional configuration is required see the documentation list below.
    def createOutputRemote(IPAddress,username,password):
        #Command line args documentation https://www.petri.com/command-line-event-log
        #How to setup remoting https://www.howtogeek.com/117192/how-to-run-powershell-commands-on-remote-computers/
        #Powershell command for remote machines
            #This command will only check the 100 most recent event logs. Change or remove the /c:{#} to increase or decrease this threshold
        myCmd = f"powershell.exe $secureString = '{password}' | ConvertTo-SecureString -AsPlainText -Force; $credential = New-Object pscredential('{username}', $secureString); Invoke-Command -ComputerName {IPAddress}" + " -ScriptBlock {wevtutil qe Microsoft-Windows-PrintService/Operational /rd:true /f:text } -Credential $credential"
        #executes command on remote machines powershell
        output = subprocess.Popen(myCmd,stdout=subprocess.PIPE)
        logger.warning("Output: %s", output)
        readOutput = output.stdout.read()

        #Response from remote machine is encrypted as bytes you must decode to make data readable
        decodeOutput = readOutput.decode("utf-8")

        #Turns output into a list
        outputList = decodeOutput.splitlines()
        logger.warning("OutputList: %s", outputList)
        #Local variables that hold all information from log output
        #!IMPORTANT! If you want to use a different event change the listNames, the if startswith statements, the list name infron to of the append function, and the text inside the Regex
        eventNum = []
        logName = []
        logSource = []
        date = []
        eventId = []
        task = []
        level = []
        opcode = []
        computer = []
        description = []
        bytesize = []
        value = []

        #For loop that breaks apart the command line return and uses regex to remove and white spaces as and the value in front of the actual data.
            #List name above should be the same whatever is being regexed out of the line
        event = 0
        for index, line in enumerate(outputList):
            if line.startswith('Event'):
                eventNum.append(event)
                event = event + 1
            elif line.startswith('  Log Name:'):
                logName.append(re.sub(r"(.*)\ Log Name: ","",line))
            elif line.startswith('  Source:'):
                logSource.append(re.sub(r"(.*)\ Source: ","",line))
            elif line.startswith('  Date:'):
                date.append(re.sub(r"(.*)\Date: ","",line))
            elif line.startswith('  Event ID:'):
                eventId.append(re.sub(r"(.*)\ Event ID: ","",line))
            elif line.startswith('  Task:'):
                task.append(re.sub(r"(.*)\ Task: ","",line))
            elif line.startswith('  Level:'):
                level.append(re.sub(r"(.*)\ Level: ","",line))
            elif line.startswith('  Opcode:'):
                opcode.append(re.sub(r"(.*)\ Opcode: ","",line))
            elif line.startswith('  Computer:'):
                computer.append(re.sub(r"(.*)\ Computer: ","",line))
            elif line.startswith('  Description:'):
                description.append(outputList[index+1])

        #Extracts a certain value from a part of the log description in this case we are extracting the bytes amount from the description of a log
        for index, type in enumerate(task):
            if type == 'Printing a document':
                bytesize.append(re.search(r"Size in bytes: (.*?)\.", description[index]).group(1))
                value.append(index)
        byteAsNumber = list(map(int, bytesize))
        return eventNum, logName, logSource, date, eventId, task, level, opcode, computer, description, byteAsNumber, value

    #Turns data obtained from the above methods into JSON dictionaries. For a specific value
    def getBytes(logName,date, task, level, opcode, computer, byteAsNumber, value):
        #Creates and populates lists for logs that only have byte values
        dictName = []
        dictDate = []
        dictTask = []
        dictLevel = []
        dictOpCode = []
        dictComputer = []
        dictBytes = []

        for index, i in enumerate(value):
            dictName.append(logName[i])
            dictDate.append(date[i])
            dictTask.append(task[i])
            dictLevel.append(level[i])
            dictOpCode.append(opcode[i])
            dictComputer.append(computer[i])
            dictBytes.append(byteAsNumber[index])

        #Dictionary that takes the above lists and funnel them into dictionary that makes it easy to pull data in the actual plugin.
        dict={}
        dict.setdefault('Name',[])
        dict.setdefault('Date',[])
        dict.setdefault('Task',[])
        dict.setdefault('Level',[])
        dict.setdefault('OpCode',[])
        dict.setdefault('Computer',[])
        dict.setdefault('Bytes',[])

        #add the list values to the dictionary
        for index, entry in enumerate(dictBytes):
            dict['Name'].append(dictName[index])
            dict['Date'].append(dictDate[index])
            dict['Task'].append(dictTask[index])
            dict['Level'].append(dictLevel[index])
            dict['OpCode'].append(dictOpCode[index])
            dict['Computer'].append(dictComputer[index])
            dict['Bytes'].append(dictBytes[index])
        #Turn the dictionary into a json format
        jsonData = json.dumps(dict, indent=4)
        loadJson = json.loads(jsonData)
        logger.warning(loadJson)
        return loadJson

    #gets all unique names for PC
    def get_computer_names(computerList):
            uniqueComputerName = []
            for item in computerList:
                if item not in uniqueComputerName:
                    uniqueComputerName.append(item)
            return uniqueComputerName

if __name__ == '__main__':
    eventParser()
