#! /usr/bin/env python

import sys
import getopt
import optparse
import commands
    
def returnStatus(statusInfo,checkMode):
    statusResult = None
    output = ""
    failCount = 0
    successCount = 0
    for line in statusInfo:
        cStatus = line[0]
        cOutput = line[1].replace("\n"," ")        
        output = cOutput + "\n"
        if cStatus > 0:
            failCount = failCount + 1
        if cStatus == 0:
            successCount = successCount + 1
    
    counts = str(failCount)+ " failed "+str(successCount)+ " succeeded"
    
    returnCode = 3
    if checkMode == "one":
        if successCount > 0:
            returnCode = 0
        else:
            returnCode = 2
    elif checkMode == "all":
        if failCount == 0:
            returnCode = 0
        else:
            returnCode = 2
    
    if returnCode == 0:
        output = "MULTIPLE CHECK OK: " + counts + "\n"+ output
    elif returnCode >0:
        output = "MULTIPLE CHECK CRITICAL: " + counts + "\n"+ output
        
    print output
    sys.exit(returnCode);
    
def runCommands(commandList):
    statusInfo = []
    #loop through all the commands
    for i in commandList:
        i = i.lstrip().rstrip()        
        #run the command
        (cStatus,cOutput) = commands.getstatusoutput(i)
        #store the result
        statusInfo.insert(0,[cStatus,cOutput])
    return statusInfo
    
def main():
    parser = optparse.OptionParser()
    parser.add_option("--commands",dest="commands",help="string of commands to run. enclose in quotes. seperate each command by @#%  eg command1@#%command2")
    parser.add_option("--mode",dest="mode",help="specify 'one' or 'all'.  'one' will return true if any one of the checks is successfull. 'all' will return false if any one of the checks fail. default is all")
    (options, args) = parser.parse_args(sys.argv[1:])

    #set checkMode
    checkMode = "all"
    if not options.mode or options.mode == "all":
        checkMode = "all"
    elif options.mode == "one":
        checkMode = "one"

    #ensure commands were specified
    if not options.commands:
        print "no commands specified"
        sys.exit(3)
        return
    
    commandList = options.commands.split("@#%")

    #run the commands
    commandsStatus = runCommands(commandList)  
    
    #process the results
    returnStatus(commandsStatus,checkMode)


if __name__ == "__main__":
    main()
