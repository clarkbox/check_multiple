# check_multiple

Nagios plugin used to execute multiple commands in parlallel. It can be configured to return failure if one command fails, or only if they all fail.

An example command that will ping a host and check that HTTP/SSH are running on it:

```
define command{
command_name check-host-alive-multiple

command_line $USER1$/check_multiple --mode one "$USER1$/check_ping -H $HOSTADDRESS$ -w 1000.0,80% -c 1000.0,100% -p 5" "$USER1$/check_http -H $HOSTADDRESS$" "USER1$/check_ssh -H $HOSTADDRESS$"
}
```

Run from the command line:
```
usage: check_multiple.py [-h] [--mode {all,one}] command [command ...]

Run multiple Nagios checks and combine the results.

positional arguments:
  command           check to run, enclosed in quotes

optional arguments:
  -h, --help        show this help message and exit
  --mode {all,one}  which individual checks must succeed before the whole
                    check does; either "one" or "all" of them (default: all)
```

Run the test suite:
```
$ python -m unittest check_multiple.py
........
----------------------------------------------------------------------
Ran 8 tests in 0.928s

OK
```
