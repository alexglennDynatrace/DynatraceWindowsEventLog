import os
import re
import logging
import json
#Imports the other python file that creates the information read by Dynatrace
from EventParser import eventParser
#Dynatrace Plugin SDK
from ruxit.api.base_plugin import RemoteBasePlugin

logger = logging.getLogger(__name__)

#!IMPORTANT! This plugin is designed to work only for Windows machines. Powershell is required for this to work. Additional configuration may be required if machine is not in the same domain as the Acitivegate
class WindowsEventLog(RemoteBasePlugin):

    #Were global variables are set in format self.{variablename} = aValue
    def initialize(self, **kwargs):
        config = kwargs['config']

        #Input from enpoint setup is made here self.{endpointKey} = self.config.get("endpointKey","DefaultValue")
            #Default value is set so if there is no input there is at least some value in them
        self.user = self.config.get("user","admin")
        self.password = self.config.get("password", "admin")
        self.ipaddress = self.config.get("machine_name","110.1.1.1" )
        self.isRemote = self.config.get("remote_machine", True)

        #Sets list that enters only new Byte values into Dynatrace
        self.unique_bytes = []

    def query(self, **kwargs):
        #Create group - provide group id used to calculate unique entity id in dynatrace and display name for UI presentation
            #Change name of create_group if you want to use a different event log
        group = self.topology_builder.create_group("Windows Print Queue", "Windows Print Queue")

        #Checks to see if the plugin is trying to reach out to a remote machine. If it is not the plugin will look at the Local machines event logs
        if self.isRemote == False:
            #Creates values for all lines of the log files
            localEventNum, localLogName, localLogSource, localDate, localEventId, localTask, localLevel, localOpcode, localComputer, localDescription, localByteAsNumber, localValue = eventParser.createOutputLocal()

            #creates a json dictionary for Byte values making it easier to search and read
            localJson = eventParser.getBytes(localLogName, localDate, localTask, localLevel, localOpcode, localComputer, localByteAsNumber, localValue)

            #Populates Device Values
            printerComputer = eventParser.get_computer_names(localJson['Computer'])

            #Populates bytes value
            bytes = localJson['Bytes']
            #logger.warning("Bytes: %s", bytes)
            #Checks through each value in Bytes and compares it to values already uploaded if the value is already present it is ignored. If the value is now it is added to the self.unique_bytes list.
                #Nested for loop ensures that the byte value is from the correct device
            for device in printerComputer:
                device = group.create_device("Print_Service",device)
                for newValue in bytes:
                    if newValue not in self.unique_bytes:
                        self.unique_bytes.append(newValue)
                        #Uploads the Byte value to Dynatrace
                        device.absolute(key='counter', value=newValue)
                        logger.warning("Bytes Value = %s ", newValue )

        elif self.isRemote == True:
            #Creates values for all lines of the log files
            logger.warning("Executing Remote Query")
            remoteEventNum, remoteLogName, remoteLogSource, remoteDate, remoteEventId, remoteTask, remoteLevel, remoteOpcode, remoteComputer, remoteDescription, remoteByteAsNumber, remoteValue = eventParser.createOutputRemote(self.ipaddress, self.user, self.password)

            #creates a json dictionary for Byte values making it easier to search and read
            remoteJson = eventParser.getBytes(remoteLogName, remoteDate, remoteTask, remoteLevel, remoteOpcode, remoteComputer, remoteByteAsNumber, remoteValue)
            logger.warning("RemoteJSON: %s",remoteJson)
            #Populates Device Values
            printerComputer = eventParser.get_computer_names(remoteJson['Computer'])
            logger.warning(printerComputer)
            #Populates bytes value
            bytes = remoteJson['Bytes']
            logger.warning("Bytes: %s", bytes)
            #Checks through each value in Bytes and compares it to values already uploaded if the value is already present it is ignored. If the value is now it is added to the self.unique_bytes list.
                #Nested for loop ensures that the byte value is from the correct device
            for device in printerComputer:
                device = group.create_device("Print_Service",device)
                logger.warning(device)
                for newValue in bytes:
                    logger.warning(newValue)
                    if newValue not in self.unique_bytes:
                        self.unique_bytes.append(newValue)
                        logger.warning("Bytes Value = %s ", newValue )
                        device.absolute(key='counter', value=newValue)

# foo = WindowsEventLog()
# foo.query()
