# Example entry point for unit tests


import unittest

def main():
    test_loader = unittest.TestLoader()

    tests = test_loader.discover('.')

    unittest.TextTestRunner(failfast=False).run(tests)


if __name__ == '__main__':
    main()

