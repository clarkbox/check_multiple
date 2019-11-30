#!/usr/bin/env python2.7

import sys
import argparse
import subprocess
from multiprocessing.pool import ThreadPool


def return_status(status_info, check_mode):
    output = ""
    fail_count = 0
    success_count = 0
    for line in status_info:
        c_status = line[0]
        c_output = line[1].replace("\n", " ")
        output += c_output + "\n"
        if c_status > 0:
            fail_count = fail_count + 1
        if c_status == 0:
            success_count = success_count + 1

    counts = str(fail_count) + " failed " + str(success_count) + " succeeded"

    return_code = 3
    if check_mode == "one":
        if success_count > 0:
            return_code = 0
        else:
            return_code = 2
    elif check_mode == "all":
        if fail_count == 0:
            return_code = 0
        else:
            return_code = 2

    if return_code == 0:
        output = "MULTIPLE CHECK OK: " + counts + "\n" + output
    elif return_code > 0:
        output = "MULTIPLE CHECK CRITICAL: " + counts + "\n" + output

    print(output)
    sys.exit(return_code)


class Task(object):

    exitcode = None
    output = ''

    def __init__(self, cmd):
        self.cmd = cmd

    def __call__(self):
        p = subprocess.Popen(
            self.cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.output, _ = p.communicate()
        self.exitcode = p.returncode


def run_commands(command_list):
    tasks = []
    pool = ThreadPool(5)
    for i in command_list:
        i = i.lstrip().rstrip()
        task = Task(i)
        pool.apply_async(task)
        tasks.append(task)

    pool.close()
    pool.join()

    status_info = []
    for task in tasks:
        status_info.insert(0, [task.exitcode, task.output])
    return status_info


def main():
    parser = argparse.ArgumentParser(
        description='Run multiple Nagios checks at once.')
    parser.add_argument(
        "--mode",
        default='all',
        choices=['all', 'one'],
        help="Specify `one` or `all`. `one` will return OK if any one of the "
        "checks is successfull. `all` will return CRITICAL if any one of the "
        "checks fail. default is `all`.")
    parser.add_argument(
        "command",
        nargs="+",
        help="Checks to run. Enclose (separately) in quotes.")

    args = parser.parse_args()

    commands_status = run_commands(args.command)
    return_status(commands_status, args.mode)


if __name__ == "__main__":
    main()
