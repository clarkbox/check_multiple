#!/usr/bin/python3

import sys
import argparse
import subprocess
from multiprocessing.pool import Pool


def process_results(results, check_mode):
    """
    Process the list of individual (exitcode, output) `results`
    according to `check_mode`, and return an overall (exitcode,
    output) pair.
    """
    output = ""
    fail_count = 0
    success_count = 0

    for (c_status, c_output) in results:
        if c_status == 0:
            success_count += 1
        else:
            fail_count += 1
        if len(c_output) > 0:
            output += c_output.replace("\n", " ") + "\n"

    counts = str(fail_count) + " failed, " + str(success_count) + " succeeded"

    return_code = 0
    if check_mode == "one" and success_count == 0:
        return_code = 2
    if check_mode == "all" and fail_count != 0:
        return_code = 2

    result_string = "OK"
    if return_code != 0:
        result_string = "CRITICAL"

    output = "MULTIPLE CHECK " + result_string + ": " + counts + "\n" + output
    return (return_code, output)


def run_command(c):
    """
    Run a single command in a shell, capturing its output as text.

    Returns a single CompletedProcess instance.
    """
    # The "capture_output=True" keyword argument that we would like to
    # pass to run() doesn't exist before python-3.7. Likewise, the
    # "universal_newlines" argument has been renamed to "text", but
    # only in python 3.7.
    return subprocess.run(c,
                          shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          universal_newlines=True)


def run_commands(command_list):
    """
    Run a list of commands, and return a list of (exitcode, output) pairs.
    """
    pool = Pool()
    results = pool.map(run_command, command_list)
    pool.close()
    pool.join()

    return [ (result.returncode, result.stdout) for result in results ]


def main():
    parser = argparse.ArgumentParser(
        description='Run multiple Nagios checks and combine the results.')
    parser.add_argument(
        "--mode",
        default='all',
        choices=['all', 'one'],
        help="which individual checks must succeed before the whole check "
             "does; either \"one\" or \"all\" of them (default: all)")
    parser.add_argument(
        "command",
        nargs="+",
        help="check to run, enclosed in quotes")

    args = parser.parse_args()
    exitcode,output = process_results(run_commands(args.command), args.mode)
    print(output)
    sys.exit(exitcode)

if __name__ == "__main__":
    main()
