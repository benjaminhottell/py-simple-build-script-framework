# Sample SBSF script for a Python module


import typing as ty
import os
import shutil
import sbsf


CWD = os.getcwd()

# Path to Python 3 executable, or its name on PATH
PYTHON3 = os.getenv('PYTHON3', 'python3')

# Name of the package (found in src/PKG_NAME)
PKG_NAME = 'helloworld'

# Name of tests package
TESTS = 'tests'

# Path to the testing virtual environment
VENV_TEST = os.path.join(CWD, 'venv', 'test')

# Path to pip within the testing virtual environment
VENV_TEST_PIP = os.path.join(VENV_TEST, 'bin', 'pip3')

# Path to python3 within the testing virtual environment
VENV_TEST_PY = os.path.join(VENV_TEST, 'bin', 'python3')


def _get_env():
    ret = dict(os.environ)
    ret['PYTHONPATH'] = './src:'+ret['PYTHONPATH']
    return ret


def _cmd(ctx: sbsf.TargetContext, args: ty.Sequence[str|os.PathLike]):
    return ctx.run(args, env=_get_env())


builder = sbsf.new_builder()


@builder.target(
    'setup-venv-test',
    help='Set up the test virtual environment',
)
def target_setup_venv_test(ctx: sbsf.TargetContext):
    if os.path.exists(VENV_TEST):
        return
    _cmd(ctx, [PYTHON3, '-m', 'venv', VENV_TEST])
    _cmd(ctx, [VENV_TEST_PIP, 'install', 'mypy'])


@builder.target(
    'lint-test',
    help='Perform static analysis on the tests package',
    needs=['setup-venv-test'],
)
def target_lint_test(ctx: sbsf.TargetContext):
    _cmd(ctx, [VENV_TEST_PY, '-m', 'mypy', TESTS])


@builder.target(
    'lint-src',
    help='Perform static analysis on the src directory',
    needs=['setup-venv-test'],
)
def target_lint_src(ctx: sbsf.TargetContext):
    _cmd(ctx, [VENV_TEST_PY, '-m', 'mypy', 'src'])


builder.add_target(
    'lint',
    help='Perform static analysis on all source files, including tests',
    needs=['lint-src', 'lint-test'],
)


@builder.target(
    'test-no-lint',
    help='Execute tests without involving static analysis',
    needs=['setup-venv-test'],
)
def target_test_no_lint(ctx: sbsf.TargetContext):
    _cmd(ctx, [VENV_TEST_PY, '-m', TESTS])


builder.add_target(
    'test',
    help='Perform static analysis and run all tests',
    needs=['lint', 'test-no-lint'],
)


def _clean(file: str|os.PathLike) -> None:
    if os.path.exists(file):
        shutil.rmtree(file)

@builder.target(
    'clean',
    help='Remove machine-generated files',
)
def target_clean(ctx: sbsf.TargetContext):
    del ctx
    _clean('mypy_cache')
    _clean('venv')


if __name__ == '__main__':
    import sys
    sys.exit(builder.cli_main())

