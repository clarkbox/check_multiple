#!/usr/bin/python3

import sys
import argparse
import subprocess
import unittest
from multiprocessing.pool import Pool

# Return codes specified by the Nagios plugin API.
EXIT_OK = 0
EXIT_WARNING = 1
EXIT_CRITICAL = 2
EXIT_UNKNOWN = 3

def process_results(results, check_mode):
    """
    Process the list of individual (exitcode, output) `results`
    according to `check_mode`, and return an overall (exitcode,
    output) pair.
    """
    output = ""
    critical_count = 0
    ok_count = 0

    for (c_status, c_output) in results:
        if c_status == 0:
            ok_count += 1
        else:
            critical_count += 1
        if len(c_output) > 0:
            output += c_output.replace("\n", " ") + "\n"

    counts = str(critical_count) + " critical, " + str(ok_count) + " ok"

    return_code = EXIT_OK
    if check_mode == "one" and ok_count == 0:
        return_code = EXIT_CRITICAL
    if check_mode == "all" and critical_count != 0:
        return_code = EXIT_CRITICAL

    result_string = "OK"
    if return_code != EXIT_OK:
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



class ExitCodeTestCase(unittest.TestCase):
    """
    Run the shell commands "true" and "false" in parallel to ensure
    that our return code is what we think it should be.
    """
    def test_mode_one_true_true_exit_code(self):
        exitcode,_ = process_results(run_commands(["true", "true"]), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_true_false_exit_code(self):
        exitcode,_ = process_results(run_commands(["true", "false"]), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_false_true_exit_code(self):
        exitcode,_ = process_results(run_commands(["false", "true"]), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_false_false_exit_code(self):
        exitcode,_ = process_results(run_commands(["false", "false"]), "one")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_true_true_exit_code(self):
        exitcode,_ = process_results(run_commands(["true", "true"]), "all")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_all_true_false_exit_code(self):
        exitcode,_ = process_results(run_commands(["true", "false"]), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_false_true_exit_code(self):
        exitcode,_ = process_results(run_commands(["false", "true"]), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_false_false_exit_code(self):
        exitcode,_ = process_results(run_commands(["false", "false"]), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)
