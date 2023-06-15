import unittest

from ocdb.api import utils


class TestUtils(unittest.TestCase):
    def test_encrypt(self):
        res = utils.encrypt('password')
        self.assertEqual('b109f3bbbc244eb82441917ed06d618b9008dd09b3befd1b5e07394c706a8b'
                         'b980b1d7785e5976ec049b46df5f1326af5a2ea6d103fd07c95385ffab0cacbc86', res)


if __name__ == '__main__':
    unittest.main()
