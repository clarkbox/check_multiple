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
EXIT_STRINGS = ["OK",
                "WARNING",
                "CRITICAL",
                "UNKNOWN"]

def process_results(results, check_mode):
    """
    Process the list of individual (exitcode, output) `results`
    according to `check_mode`, and return an overall (exitcode,
    output) pair.
    """
    statuses = [ status for (status,_) in results ]
    critical_count = len([ s for s in statuses if s == EXIT_CRITICAL ])
    warning_count  = len([ s for s in statuses if s == EXIT_WARNING ])
    ok_count       = len([ s for s in statuses if s == EXIT_OK ])

    suboutput = "\n".join(
        [ c_output.replace("\n", " ") for (_,c_output) in results
                                      if len(c_output) > 0 ] )

    counts  = str(critical_count) + " critical, "
    counts += str(warning_count) + " warning, "
    counts += str(ok_count) + " ok"

    return_code = EXIT_OK
    worst_status = max(statuses)
    best_status = min(statuses)
    if check_mode == "one" and best_status != EXIT_OK:
        # We won't get an overall OK unless an individual status was
        # OK... but if the individual statuses are all WARNING, then
        # we should return WARNING as well, and not CRITICAL.
        return_code = best_status
    if check_mode == "all" and worst_status != EXIT_OK:
        # If any check was not OK, then we want to return the worst
        # not-OK status. If there was one warning and a bunch of OKs,
        # then we want to return WARNING. If anything was critical, we
        # want to return critical.
        return_code = worst_status

    output = "MULTIPLE CHECK " + EXIT_STRINGS[return_code]
    output += ": " + counts + "\n" + suboutput
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



ok = "exit " + str(EXIT_OK)
warning = "exit " + str(EXIT_WARNING)
critical = "exit " + str(EXIT_CRITICAL)
class ExitCodeTestCase(unittest.TestCase):
    """
    Run the shell commands "true" and "false" in parallel to ensure
    that our return code is what we think it should be.
    """

    #
    # Mode "one", all 3^3 possible results for three commands.
    #
    def test_mode_one_ok_ok_ok_exit_code(self):
        commands = [ok, ok, ok]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_ok_warning_exit_code(self):
        commands = [ok, ok, warning]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_ok_critical_exit_code(self):
        commands = [ok, ok, critical]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_warning_ok_exit_code(self):
        commands = [ok, warning, ok]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_warning_warning_exit_code(self):
        commands = [ok, warning, warning]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_warning_critical_exit_code(self):
        commands = [ok, warning, critical]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_critical_ok_exit_code(self):
        commands = [ok, critical, ok]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_critical_warning_exit_code(self):
        commands = [ok, critical, warning]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_critical_critical_exit_code(self):
        commands = [ok, critical, critical]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_ok_ok_exit_code(self):
        commands = [warning, ok, ok]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_ok_warning_exit_code(self):
        commands = [warning, ok, warning]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_ok_critical_exit_code(self):
        commands = [warning, ok, critical]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_warning_ok_exit_code(self):
        commands = [warning, warning, ok]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_warning_warning_exit_code(self):
        commands = [warning, warning, warning]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_warning_warning_critical_exit_code(self):
        commands = [warning, warning, critical]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_warning_critical_ok_exit_code(self):
        commands = [warning, critical, ok]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_critical_warning_exit_code(self):
        commands = [warning, critical, warning]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_warning_critical_critical_exit_code(self):
        commands = [warning, critical, critical]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_critical_ok_ok_exit_code(self):
        commands = [critical, ok, ok]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_critical_ok_warning_exit_code(self):
        commands = [critical, ok, warning]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_critical_ok_critical_exit_code(self):
        commands = [critical, ok, critical]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_critical_warning_ok_exit_code(self):
        commands = [critical, warning, ok]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_critical_warning_warning_exit_code(self):
        commands = [critical, warning, warning]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_critical_warning_critical_exit_code(self):
        commands = [critical, warning, critical]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_critical_critical_ok_exit_code(self):
        commands = [critical, critical, ok]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_critical_critical_warning_exit_code(self):
        commands = [critical, critical, warning]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_critical_critical_critical_exit_code(self):
        commands = [critical, critical, critical]
        exitcode,_ = process_results(run_commands(commands), "one")
        self.assertEqual(exitcode, EXIT_CRITICAL)


    #
    # Mode "all", all 3^3 possible results for three commands.
    #
    def test_mode_all_ok_ok_ok_exit_code(self):
        commands = [ok, ok, ok]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_all_ok_ok_warning_exit_code(self):
        commands = [ok, ok, warning]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_ok_ok_critical_exit_code(self):
        commands = [ok, ok, critical]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_ok_warning_ok_exit_code(self):
        commands = [ok, warning, ok]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_ok_warning_warning_exit_code(self):
        commands = [ok, warning, warning]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_ok_warning_critical_exit_code(self):
        commands = [ok, warning, critical]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_ok_critical_ok_exit_code(self):
        commands = [ok, critical, ok]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_ok_critical_warning_exit_code(self):
        commands = [ok, critical, warning]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_ok_critical_critical_exit_code(self):
        commands = [ok, critical, critical]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_warning_ok_ok_exit_code(self):
        commands = [warning, ok, ok]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_warning_ok_warning_exit_code(self):
        commands = [warning, ok, warning]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_warning_ok_critical_exit_code(self):
        commands = [warning, ok, critical]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_warning_warning_ok_exit_code(self):
        commands = [warning, warning, ok]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_warning_warning_warning_exit_code(self):
        commands = [warning, warning, warning]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_warning_warning_critical_exit_code(self):
        commands = [warning, warning, critical]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_warning_critical_ok_exit_code(self):
        commands = [warning, critical, ok]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_warning_critical_warning_exit_code(self):
        commands = [warning, critical, warning]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_warning_critical_critical_exit_code(self):
        commands = [warning, critical, critical]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_ok_ok_exit_code(self):
        commands = [critical, ok, ok]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_ok_warning_exit_code(self):
        commands = [critical, ok, warning]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_ok_critical_exit_code(self):
        commands = [critical, ok, critical]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_warning_ok_exit_code(self):
        commands = [critical, warning, ok]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_warning_warning_exit_code(self):
        commands = [critical, warning, warning]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_warning_critical_exit_code(self):
        commands = [critical, warning, critical]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_critical_ok_exit_code(self):
        commands = [critical, critical, ok]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_critical_warning_exit_code(self):
        commands = [critical, critical, warning]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_critical_critical_exit_code(self):
        commands = [critical, critical, critical]
        exitcode,_ = process_results(run_commands(commands), "all")
        self.assertEqual(exitcode, EXIT_CRITICAL)
