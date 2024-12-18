import unittest

import sbsf


class TestSimpleUsage(unittest.TestCase):

    def test_target_executed(self):

        count_build = 0
        count_run = 0

        builder = sbsf.new_builder()

        def build_func():
            nonlocal count_build
            count_build += 1

        builder.add_target(
            name='build',
            help='Build/compile all necessary files',
            function=lambda _: build_func(),
        )

        @builder.target(
            name='run',
            help='Run the project',
            needs=['build'],
        )
        def target_run(ctx: sbsf.TargetContext):
            del ctx  # silence linter
            nonlocal count_run
            count_run += 1

        del target_run  # silence linter

        # Test invoking direclty

        builder.resolve_targets(['build', 'run'])

        self.assertEqual(count_build, 1)
        self.assertEqual(count_run, 1)

        # Test invoking with CLI args

        builder.cli_main(['--', 'build'])

        self.assertEqual(count_build, 2)
        self.assertEqual(count_run, 1)

        # Test that the dependency 'build' is resolved whenever 'run' is resolved

        builder.resolve_targets(['run'])

        self.assertEqual(count_build, 3)
        self.assertEqual(count_run, 2)

