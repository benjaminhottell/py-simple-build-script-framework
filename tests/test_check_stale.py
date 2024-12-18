import unittest

import tempfile
import os
import time

import sbsf


class TestCheckStale(unittest.TestCase):

    def test_check_stale(self):

        count_hello = 0
        count_intro = 0

        with tempfile.TemporaryDirectory() as temp_dir:

            hello_path = os.path.join(temp_dir, 'hello.txt')
            intro_path = os.path.join(temp_dir, 'intro.txt')

            builder = sbsf.new_builder()

            @builder.target(
                name='hello.txt',
                help='Generate hello.txt',
            )
            def target_hello(ctx: sbsf.TargetContext):

                if not ctx.check_stale([], [hello_path]):
                    return

                nonlocal count_hello
                count_hello += 1

                with open(hello_path, 'w') as out_file:
                    out_file.write('Hello, world\n')


            @builder.target(
                name='intro.txt',
                help='Generate intro.txt',
                needs=['hello.txt'],
            )
            def target_intro(ctx: sbsf.TargetContext):

                if not ctx.check_stale([hello_path], [intro_path]):
                    return

                nonlocal count_intro
                count_intro += 1

                with open(intro_path, 'w') as out_file:
                    with open(hello_path, 'r') as in_file:
                        out_file.write(in_file.read())
                    out_file.write('My name is ___\n')

            # silence linter
            del target_hello
            del target_intro


            # Pass 1: hello.txt and intro.txt should be created

            builder.resolve_targets(['intro.txt'])

            self.assertEqual(count_hello, 1)
            self.assertEqual(count_intro, 1)

            with open(intro_path) as in_file:
                value = in_file.read()
                self.assertEqual(value, 'Hello, world\nMy name is ___\n')
                del value


            # Pass 2: nothing should happen

            builder.resolve_targets(['intro.txt'])

            self.assertEqual(count_hello, 1)
            self.assertEqual(count_intro, 1)


            # Pass 3: delete intro, hello should not be re-made

            os.unlink(intro_path)

            builder.resolve_targets(['intro.txt'])

            self.assertEqual(count_hello, 1)
            self.assertEqual(count_intro, 2)


            # Pass 4: delete hello, both should be re-made

            os.unlink(hello_path)

            # Wait for a tiny bit to make sure that hello's mtime is clearly different from intro's mtime
            time.sleep(0.05)

            builder.resolve_targets(['intro.txt'])

            self.assertEqual(count_hello, 2)
            self.assertEqual(count_intro, 3)

