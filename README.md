# check_multiple

Nagios plugin used to execute multiple commands in series. It can be configured to fail if one command fails, or only if they all fail.

Example command that will check SSH and ping host:
```
define command{
command_name check-host-alive-multiple

command_line $USER1$/check_multiple --mode one --commands "$USER1$/check_ping -H $HOSTADDRESS$ -w 1000.0,80% -c 1000.0,100% -p 5@#%$USER1$/check_http -H $HOSTADDRESS$@#%$USER1$/check_ssh -H $HOSTADDRESS$"
}
```

Run from the command line:
```
usage: check_multiple.py [-h] [--mode {all,one}] commands [commands ...]

Run multiple Nagios checks at once.

positional arguments:
  commands          Checks to run. Enclose (separately) in quotes.

optional arguments:
  -h, --help        show this help message and exit
  --mode {all,one}  Specify `one` or `all`. `one` will return OK if any one of
                    the checks is successfull. `all` will return CRITICAL if
                    any one of the checks fail. default is `all`.

```
