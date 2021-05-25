import os
import sys
import glob
import subprocess

from check import check

def main():
    # validate input
    try:
        # modules to test
        modules_dir = sys.argv[1]
        modules = []
        for path in glob.glob(modules_dir + "/*"):
            modules.append(os.path.relpath(path))
        # inputs to test against
        inputs_dir = sys.argv[2]
        inputs = []
        for path in glob.glob(inputs_dir + "/*.json"):
            with open(path) as file:
                inputs.append((os.path.abspath(path), file.read()))
        inputs[0] # ensure non-empty
        reports_dir = sys.argv[3]
    except IndexError:
        print("not enough arguments", file=sys.stderr)
        print(
            "usage:",
            "python3 autocheck <modules dir> <inputs dir> <reports dir>",
            file=sys.stderr,
        )
        sys.exit(1)
    except FileNotFoundError as e:
        print("error:", e, file=sys.stderr)
        sys.exit(2)
    
    for module in modules:
        # run module and validate output
        print("---")
        print("testing", module)
        report = os.path.join(reports_dir, os.path.basename(module)+".txt")
        with open(report, 'w') as report:
            run_module_all(module, inputs, report)


def run_module_all(module, inputs, reportfile):
    correct = 0
    for t, (path, data_text) in enumerate(sorted(inputs), 1):
        print(f"test {t:02d}:", os.path.basename(path))
        print(f"test {t:02d}:", os.path.basename(path), file=reportfile)
        try:
            soln_text = run_module_once(module, path)
            # TODO: Catch different types of validation issues
            check(data_text, soln_text, verbose=False)
            # TODO: Print some kind of report, and total, for the student
            result = "solved!"
            correct += 1
        except TimesUp:
            result = "TIMEOUT"
        except NonZeroExit as e:
            result = f"ERRORED {e}"
        except Exception as e:
            result = f"INVALID {e}"
        print("↪", result)
        print("↪", result, file=reportfile)
    print(
        module,
        "summary:",
        f"{correct} / {len(inputs)} ({correct / len(inputs):.2%})",
    )
    print(
        "summary:",
        f"{correct} / {len(inputs)} ({correct / len(inputs):.2%})",
        file=reportfile
    )
    return correct


def run_module_once(module, path):
    """
    Runs python module `module` on command-line input `path`, with three
    possible outcomes:
    1. Successfully execute: return stdout
    2. Run-time error, non-zero exit: raise Exception
    3. Time-out: raise subprocess.TimeoutExpired
    """
    try:
        result = subprocess.Popen(
                args=["python3", "-m", "search", path],
                cwd=module,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        result.stdout, result.stderr = result.communicate(
                timeout=TimesUp.LIMIT,
            )
    except subprocess.TimeoutExpired:
        raise TimesUp(f"time limit expired ({TimesUp.LIMIT} seconds)")
    if result.returncode != 0:
        raise NonZeroExit(f"non-zero exit; stderr:\n{result.stderr}")
    else:
        return result.stdout

class NonZeroExit(Exception):
    """For an error from the called module"""

class TimesUp(Exception):
    """For when the called module exceeds the time limit"""
    LIMIT = 30 # seconds

if __name__ == "__main__":
    main()



