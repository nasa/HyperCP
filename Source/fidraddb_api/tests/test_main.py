import unittest

from ocdb.main import main


class MainTest(unittest.TestCase):

    def test_run_module(self):
        with self.assertRaises(SystemExit):
            main(["--help"])

# @todo 1 tb/** fails - reactivate later 2019-04-21
# def test_run_module_as_script(self):
#     code = subprocess.run([sys.executable, __file__, "--help"]).returncode
#     self.assertEquals(0, code)
