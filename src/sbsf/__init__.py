import typing as ty

import argparse
import sys
import os
import subprocess
import functools
import dataclasses


TargetFunction: ty.TypeAlias = ty.Callable[['TargetContext'], ty.Any]


class TargetBenignError(RuntimeError):
    '''
    Represents an error/exception that is severe enough to abort resolving a target (and anything depending on that target), but not severe enough to end the process. (In other words, other targets may still be resolved)
    '''
    pass


@dataclasses.dataclass
class TargetInfo:
    name: str
    help: str|None


class Builder:

    def __init__(
            self,
            always_make: bool = False,
        ):
        self.always_make = always_make

        self._targets_by_name: dict[str, TargetFunction] = dict()
        self._target_helps_by_name: dict[str, str|None] = dict()

    def _wrap_with_resolver(
            self,
            func: TargetFunction,
            target_names: ty.Sequence[str],
        ) -> TargetFunction:

        @functools.wraps(func)
        def wrapper(ctx: 'TargetContext') -> ty.Any:
            for target_name in target_names:
                ctx.resolve_target(target_name)
            return func(ctx)

        return wrapper

    def add_target(
            self, 
            name: str,
            function: TargetFunction|None = None,
            help: str|None = None,
            needs: ty.Sequence[str] = tuple(),
        ) -> None:

        if name in self._targets_by_name:
            raise ValueError(f'Target name already taken: {name!r}')

        # If function is not specified, replace with a no-op
        if function is None:
            function = lambda _: None

        if len(needs) > 0:
            function = self._wrap_with_resolver(function, needs)

        self._targets_by_name[name] = function
        self._target_helps_by_name[name] = help

    def target(
            self,
            name: str,
            help: str|None = None,
            needs: ty.Sequence[str] = tuple(),
        ) -> ty.Callable[[TargetFunction], TargetFunction]:

        def decorator(target: TargetFunction) -> TargetFunction:
            self.add_target(
                name=name,
                help=help,
                needs=needs,
                function=target,
            )
            return target

        return decorator

    def create_session(self) -> 'BuildSession':
        return BuildSession(
            builder = self,
            always_make=self.always_make
        )

    def get_targets(self) -> ty.Collection[TargetInfo]:
        ret = list()

        for target_name, target_help in self._target_helps_by_name.items():
            ret.append(TargetInfo(
                name = target_name,
                help = target_help,
            ))

        return ret

    def resolve_target(self, target_name: str) -> None:
        self.create_session().resolve_target(target_name)

    def resolve_targets(self, target_names: ty.Sequence[str]) -> None:
        self.create_session().resolve_targets(target_names)

    def cli_print_targets(self, file: ty.IO[str]):
        import textwrap
        import shutil

        term_cols, term_lines = shutil.get_terminal_size()
        del term_lines

        indent = '    '

        targets = sorted(self.get_targets(), key=lambda x: x.name)

        for target in targets:

            target_help_unwrapped = target.help

            if target_help_unwrapped is None:
                target_help_unwrapped = '(No help message)'

            target_help = textwrap.wrap(target_help_unwrapped, width=term_cols - len(indent) - 1)

            print(target.name, file=file)

            for help_line in target_help:
                print(indent, end='', file=file)
                print(help_line, file=file)

            print(file=file)

    def cli_main(
            self,
            argv: ty.Sequence[str]|None = None,
            prog = 'sbsf',
            description = 'Build script using Simple Build Script Framework (sbsf)',
        ) -> int:

        if argv is None:
            argv = sys.argv[1:]

        parser = argparse.ArgumentParser(
            prog=prog,
            description=description,
        )

        parser.add_argument(
            '-B', '--always-make',
            action='store_true',
            default=False,
            help="Always re-make outputs, regardless of their cached state. Analogous to GNU Make's -B flag.",
        )

        parser.add_argument(
            '--print-targets',
            action='store_true',
            default=False,
            help="Print available target names and their help messages.",
        )

        parser.add_argument(
            'targets',
            nargs='*',
            help='The targets to execute',
        )

        args = parser.parse_args(argv)

        self.always_make = args.always_make
        print_targets = args.print_targets
        targets = args.targets

        if print_targets:
            self.cli_print_targets(file=sys.stderr)
            return 0

        if len(targets) == 0:
            print('Nothing to do.  (Use --help for usage information)', file=sys.stderr)
            return 0

        try:
            self.resolve_targets(targets)
        except TargetBenignError as e:
            print(str(e), file=sys.stderr)
            return 1

        return 0


class BuildSession:

    def __init__(
            self,
            builder: Builder,
            always_make: bool,
        ):
        self._builder = builder
        self.always_make = always_make
        self._resolved_target_names: set[str] = set()

    def _get_target_by_name(self, target_name: str):
        return self._builder._targets_by_name.get(target_name)

    def _create_target_context(self, target_name: str) -> 'TargetContext':
        return TargetContext(
            session=self,
            target_name=target_name,
            always_make=self.always_make,
        )

    def resolve_targets(self, target_names: ty.Sequence[str]) -> None:
        for target_name in target_names:
            self.resolve_target(target_name)

    def resolve_target(self, target_name: str) -> None:

        if target_name in self._resolved_target_names:
            return

        target = self._get_target_by_name(target_name=target_name)
        if target is None:
            raise ValueError(f'No such target: {target_name!r}')

        ctx = self._create_target_context(target_name=target_name)
        self._resolved_target_names.add(target_name)

        try:
            target(ctx)
        except:
            self._resolved_target_names.remove(target_name)
            raise


class TargetContext:
    '''
    This context object provides some hints and utility methods to targets while they are resolving.
    '''

    def __init__(
            self,
            session: BuildSession,
            target_name: str,
            always_make: bool,
        ):
        self._session = session
        self._target_name = target_name
        self._always_make = always_make

    @property
    def target_name(self) -> str:
        return self._target_name

    @property
    def always_make(self) -> bool:
        '''
        Set to True if targets should not skip steps if they detect their outputs are up to date. In other words, this is a hint to ignore optimizations and to re-build everything from scratch.

        Analogous to GNU Make's -B or --always-make option.
        '''
        return self._always_make

    def resolve_target(self, target_name: str) -> None:
        '''Ensures that the given target has already resolved at least once during this session.'''
        self._session.resolve_target(target_name)

    def resolve_targets(self, target_names: ty.Sequence[str]) -> None:
        '''Ensures that the given targets have already resolved at least once during this session.'''
        self._session.resolve_targets(target_names)

    def check_stale(
            self,
            inputs: ty.Collection[str|os.PathLike],
            outputs: ty.Collection[str|os.PathLike],
        ) -> bool:
        '''
        Checks if a given set of output files are 'stale' relative to a set of input files. In other words, it checks if one or more input file has an mtime greater than or equal to any of the output files.

        Outputs are always considered stale if always_make is True.
        '''

        if self._always_make:
            return True

        output_mtime = float('-inf')

        try:
            for output in outputs:
                output_mtime = max(output_mtime, os.stat(output).st_mtime)
        except FileNotFoundError:
            return True

        input_mtime = float('-inf')

        for input in inputs:
            input_mtime = max(input_mtime, os.stat(input).st_mtime)

        return input_mtime > output_mtime

    def run(
        self,
        args: ty.Sequence[str|os.PathLike],
        env: ty.Mapping[str, str],
    ) -> subprocess.CompletedProcess:

        args = [str(x) for x in args]

        try:
            return subprocess.run(args, env=env, check=True)
        except subprocess.CalledProcessError as e:
            raise TargetBenignError(e)


def new_builder() -> Builder:
    return Builder()

