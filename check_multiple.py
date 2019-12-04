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


# Numeric constants for our two modes, so that we don't have to pass
# strings around everywhere.
MODE_BEST = 0
MODE_WORST = 1

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

    worst_status = max(statuses)
    best_status = min(statuses)
    if check_mode == MODE_BEST:
        return_code = best_status
    else:
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
        default='worst',
        choices=['worst', 'best'],
        help="which individual check result should be the overall result; "
             "either the \"worst\" one or the \"best\" one (default: worst)")
    parser.add_argument(
        "command",
        nargs="+",
        help="check to run, enclosed in quotes")

    args = parser.parse_args()
    mode = MODE_WORST
    if args.mode == "best":
        mode = MODE_BEST
    exitcode,output = process_results(run_commands(args.command), mode)
    print(output)
    sys.exit(exitcode)

if __name__ == "__main__":
    main()



class ExitCodeTestCase(unittest.TestCase):
    """
    Run the shell commands "true" and "false" in parallel to ensure
    that our return code is what we think it should be.
    """

    # Shell commands that return the desired status.
    ok = "exit " + str(EXIT_OK)
    warning = "exit " + str(EXIT_WARNING)
    critical = "exit " + str(EXIT_CRITICAL)

    #
    # MODE_BEST, all 3^3 possible results for three commands.
    #
    def test_mode_one_ok_ok_ok_exit_code(self):
        commands = [self.ok, self.ok, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_ok_warning_exit_code(self):
        commands = [self.ok, self.ok, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_ok_critical_exit_code(self):
        commands = [self.ok, self.ok, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_warning_ok_exit_code(self):
        commands = [self.ok, self.warning, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_warning_warning_exit_code(self):
        commands = [self.ok, self.warning, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_warning_critical_exit_code(self):
        commands = [self.ok, self.warning, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_critical_ok_exit_code(self):
        commands = [self.ok, self.critical, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_critical_warning_exit_code(self):
        commands = [self.ok, self.critical, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_ok_critical_critical_exit_code(self):
        commands = [self.ok, self.critical, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_ok_ok_exit_code(self):
        commands = [self.warning, self.ok, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_ok_warning_exit_code(self):
        commands = [self.warning, self.ok, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_ok_critical_exit_code(self):
        commands = [self.warning, self.ok, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_warning_ok_exit_code(self):
        commands = [self.warning, self.warning, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_warning_warning_exit_code(self):
        commands = [self.warning, self.warning, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_warning_warning_critical_exit_code(self):
        commands = [self.warning, self.warning, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_warning_critical_ok_exit_code(self):
        commands = [self.warning, self.critical, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_warning_critical_warning_exit_code(self):
        commands = [self.warning, self.critical, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_warning_critical_critical_exit_code(self):
        commands = [self.warning, self.critical, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_critical_ok_ok_exit_code(self):
        commands = [self.critical, self.ok, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_critical_ok_warning_exit_code(self):
        commands = [self.critical, self.ok, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_critical_ok_critical_exit_code(self):
        commands = [self.critical, self.ok, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_critical_warning_ok_exit_code(self):
        commands = [self.critical, self.warning, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_critical_warning_warning_exit_code(self):
        commands = [self.critical, self.warning, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_critical_warning_critical_exit_code(self):
        commands = [self.critical, self.warning, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_critical_critical_ok_exit_code(self):
        commands = [self.critical, self.critical, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_one_critical_critical_warning_exit_code(self):
        commands = [self.critical, self.critical, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_one_critical_critical_critical_exit_code(self):
        commands = [self.critical, self.critical, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_BEST)
        self.assertEqual(exitcode, EXIT_CRITICAL)


    #
    # MODE_WORST, all 3^3 possible results for three commands.
    #
    def test_mode_all_ok_ok_ok_exit_code(self):
        commands = [self.ok, self.ok, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_OK)

    def test_mode_all_ok_ok_warning_exit_code(self):
        commands = [self.ok, self.ok, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_ok_ok_critical_exit_code(self):
        commands = [self.ok, self.ok, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_ok_warning_ok_exit_code(self):
        commands = [self.ok, self.warning, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_ok_warning_warning_exit_code(self):
        commands = [self.ok, self.warning, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_ok_warning_critical_exit_code(self):
        commands = [self.ok, self.warning, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_ok_critical_ok_exit_code(self):
        commands = [self.ok, self.critical, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_ok_critical_warning_exit_code(self):
        commands = [self.ok, self.critical, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_ok_critical_critical_exit_code(self):
        commands = [self.ok, self.critical, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_warning_ok_ok_exit_code(self):
        commands = [self.warning, self.ok, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_warning_ok_warning_exit_code(self):
        commands = [self.warning, self.ok, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_warning_ok_critical_exit_code(self):
        commands = [self.warning, self.ok, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_warning_warning_ok_exit_code(self):
        commands = [self.warning, self.warning, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_warning_warning_warning_exit_code(self):
        commands = [self.warning, self.warning, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_WARNING)

    def test_mode_all_warning_warning_critical_exit_code(self):
        commands = [self.warning, self.warning, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_warning_critical_ok_exit_code(self):
        commands = [self.warning, self.critical, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_warning_critical_warning_exit_code(self):
        commands = [self.warning, self.critical, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_warning_critical_critical_exit_code(self):
        commands = [self.warning, self.critical, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_ok_ok_exit_code(self):
        commands = [self.critical, self.ok, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_ok_warning_exit_code(self):
        commands = [self.critical, self.ok, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_ok_critical_exit_code(self):
        commands = [self.critical, self.ok, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_warning_ok_exit_code(self):
        commands = [self.critical, self.warning, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_warning_warning_exit_code(self):
        commands = [self.critical, self.warning, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_warning_critical_exit_code(self):
        commands = [self.critical, self.warning, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_critical_ok_exit_code(self):
        commands = [self.critical, self.critical, self.ok]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_critical_warning_exit_code(self):
        commands = [self.critical, self.critical, self.warning]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)

    def test_mode_all_critical_critical_critical_exit_code(self):
        commands = [self.critical, self.critical, self.critical]
        exitcode,_ = process_results(run_commands(commands), MODE_WORST)
        self.assertEqual(exitcode, EXIT_CRITICAL)
