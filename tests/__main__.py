# Entry point for unit tests


import unittest

from coverage import Coverage


def main():
    test_loader = unittest.TestLoader()
    cov = Coverage(source=('sbsf',))

    with cov.collect():

        # Make sure test discovery is in scope of collection
        # Otherwise, coverage.py can't capture all the data
        tests = test_loader.discover('.')

        unittest.TextTestRunner(failfast=False).run(tests)

    cov.report()
    cov.html_report(directory='htmlcov')


if __name__ == '__main__':
    main()

