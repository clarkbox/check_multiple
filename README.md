# check_multiple

This plugin will let you pass in a list of commands to be executed. It can be configured to fail if one command fails, or only if they all fail.

example command that will check SSH and ping host:
```
define command{
command_name check-host-alive-multiple

command_line $USER1$/check_multiple --mode one --commands "$USER1$/check_ping -H $HOSTADDRESS$ -w 1000.0,80% -c 1000.0,100% -p 5@#%$USER1$/check_http -H $HOSTADDRESS$@#%$USER1$/check_ssh -H $HOSTADDRESS$"
}
```

usage: check_multiple [options]
options:
-h, --help show this help message and exit
--commands=COMMANDS string of commands to run. enclose in quotes. seperate each command by @#% eg command1@#%command2

--mode=MODE specify 'one' or 'all'. 'one' will return true if any one of the checks is successfull. 'all' will return false if any one of the checks fail. default is all
