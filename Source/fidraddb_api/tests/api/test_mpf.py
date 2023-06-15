import unittest

from ocdb.api.mpf import MultiPartForm
from tests.helpers import ClientTest


class MultiPartFormTest(unittest.TestCase):

    def test_it(self):
        form = MultiPartForm(boundary="bibo")

        form.add_field("path", "BIGELOW/BALCH/gnats")

        file_obj = ClientTest.get_input_path("chl", "chl-s170604w.sub")
        form.add_file("datasetFiles",
                      "chl/chl-s170604w.sub",
                      file_obj)

        file_obj = open(ClientTest.get_input_path("chl", "chl-s170710w.sub"))
        form.add_file("datasetFiles",
                      "chl/chl-s170710w.sub",
                      file_obj)

        binary_form = bytes(form)
        # size depends on OS specific line ending characters tb 2019-04-24
        self.assertTrue(len(binary_form) > 4700)
        self.assertTrue(len(binary_form) < 4900)

        text_form = str(form)
        # size depends on OS specific line ending characters tb 2019-04-24
        self.assertTrue(len(binary_form) > 4700)
        self.assertTrue(len(binary_form) < 4900)

        self.assertTrue(text_form.startswith("--bibo\r\n"))
        self.assertTrue(text_form.endswith("--bibo--\r\n"))
