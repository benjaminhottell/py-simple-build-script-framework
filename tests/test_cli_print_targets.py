import unittest

import io
import sbsf


class TestPrintTargets(unittest.TestCase):

    def test_print_targets(self):
        builder = sbsf.new_builder()

        builder.add_target(
            name='build',
            function=lambda _: None,
        )

        builder.add_target(
            name='run',
            help='Run the application',
            function=lambda _: None,
        )

        out_file = io.StringIO()

        builder.cli_print_targets(file=out_file)

