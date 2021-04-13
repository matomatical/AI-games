# Test harness for Project Part A

This folder contains the tests and associated utilities for automatically
testing solutions to the first part of the project.

See below for details on:

* `test-creator.html`---a web-app for quickly and easily creating example
  input files.
* `autocheck.py` (and `check.py`)---scripts to validate attempted solutions.
* `test-inputs/`---the input files for the test cases themselves.

See the project specification (elsewhere) for context.

## Test generator: test-creator.html

A single-file/page webapp for easily creating test cases. Simple, if
a little hacked together (pending revision).
*They* don't build 'em like they used to, but I do!
See the app itself for instructions.

## Tests:

Mostly created with the test creator, the files inside the `test-inputs`
directory comprise the test suite to be used for assessing submissions.
There are four tests per level (so each is effectively wrth 0.25 points,
with a further 1 point available overall if the submission doesn't make
me tweak it to get the formatting to come out right).

## Test runners:


### Checking single inputs/outputs:

`check.py` is a module and script for validating a single game. You can run
it with an input file and an attempted solution output file:

```
% python3 check.py input.json output.txt
```

This script will detect any formatting or validity issues in the solution
output and exit with a non-zero exit code with 

### Checking all inputs/outputs:

`autocheck.py` is a script for validating a single implementation of the
`search` interface against a suite of test cases. It must be called from
within the directory containing the search module (due to Python path stuff),
for example like this:

```
% python3 ../tests/autocheck.py search ../tests/test-inputs/*/*.json
```

The time limit is set in the script to 30 seconds. I'm not sure yet whether
it's counting process time or wall-clock time. I'll probably lift it to be
extra permissive when running the assessment tests.
