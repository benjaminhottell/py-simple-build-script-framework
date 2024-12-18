#!/usr/bin/env python3

# To avoid a chicken-and-egg problem, sbsf does not use sbsf.


import typing as ty

import os
import sys
import subprocess


PYTHON3 = os.getenv('PYTHON3', 'python3')

CWD = os.getcwd()

SRC = os.path.join(CWD, 'src')

EXAMPLES = os.path.join(CWD, 'examples')


def get_testing_env():
    env = dict(os.environ)
    env['PYTHONPATH'] = SRC + ':' + env['PYTHONPATH']
    return env


def test_cmd(
        args: ty.Sequence[str],
        cwd: str|os.PathLike|None = None,
    ) -> subprocess.CompletedProcess:

    env = get_testing_env()

    return subprocess.run(
        args,
        check=True,
        env=env,
        cwd=cwd,
    )


def do_python_example_tests():
    example_dir = os.path.join(EXAMPLES, 'python')
    builder = os.path.join(example_dir, 'builder.py')
    test_cmd(
        [PYTHON3, builder, '--print-targets'],
        cwd=example_dir
    )
    test_cmd(
        [PYTHON3, builder, 'clean', 'clean', 'test'],
        cwd=example_dir
    )


def resolve_target(target_name: str) -> int:

    if target_name == 'test':
        test_cmd([PYTHON3, '-m', 'tests'])
        return 0

    elif target_name == 'examples':
        do_python_example_tests()
        return 0

    elif target_name == 'examples:python':
        do_python_example_tests()
        return 0

    else:
        print(f'Unrecognized target: {target_name!r}', file=sys.stderr)
        return 1


def main():
    targets = sys.argv[1:]

    for target in targets:
        try:
            code = resolve_target(target)
            if code != 0:
                sys.exit(code)
        except subprocess.CalledProcessError as e:
            print(e, file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()

