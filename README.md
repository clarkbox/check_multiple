# check_multiple

Nagios plugin used to execute multiple commands in parallel.

With the `--mode` parameter, it can be configured to return either the
best overall result, or the worst. If you choose the worst overall
result (the default), then you will be notified when one of the
commands fails. If you choose the best overall result, then you will
be notified only when all of them fail.

The output from check_multiple indicates how many OK, WARNING, and
CRITICAL results the individual commands produced. Afterwards, the
output from those individual commands, concatenated onto one line per
command, is emitted.

An example Nagios command that will ping a host and check that
HTTP/SSH are running on it, and return the best overall result
(i.e. the host is up if any service responds):

```
define command {
  command_name check-host-alive-multiple

  command_line $USER1$/check_multiple --mode best "$USER1$/check_ping -H $HOSTADDRESS$ -w 1000.0,80% -c 1000.0,100% -p 5" "$USER1$/check_http -H $HOSTADDRESS$" "USER1$/check_ssh -H $HOSTADDRESS$"
}
```

Command-line usage:

```
usage: check_multiple.py [-h] [--mode {worst,best}] command [command ...]

Run multiple Nagios checks and combine the results.

positional arguments:
  command              check to run, enclosed in quotes

optional arguments:
  -h, --help           show this help message and exit
  --mode {worst,best}  which individual check result should be the overall
                       result; either the "worst" one or the "best" one
                       (default: worst)
```

Run the test suite:
```
$ python -m unittest check_multiple.py
......................................................
----------------------------------------------------------------------
Ran 54 tests in 6.207s

OK
```

Requirements:

* Python 3.5 or greater (tested up to Python 3.8).