import os
import unittest
import warnings
from abc import ABCMeta
from typing import Dict

import httpretty

from ocdb.api.OCDBApi import OCDBApi
from ocdb.configstore import MemConfigStore
from ocdb.version import API_VERSION_TAG

TEST_URL = "http://test-server"
TEST_API_VERSION = API_VERSION_TAG


class ClientTest(unittest.TestCase, metaclass=ABCMeta):

    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*")
        os.environ['OCDB_SERVER_URL'] = TEST_URL

        self.api = OCDBApi(**self.api_kwargs)
        httpretty.enable()

    def tearDown(self):
        httpretty.disable()
        httpretty.reset()

    @property
    def api_kwargs(self) -> Dict:
        return dict(config_store=MemConfigStore(server_url=TEST_URL))

    @classmethod
    def get_input_base_dir(cls) -> str:
        return os.path.join(os.path.dirname(__file__), "res", "input")

    @classmethod
    def get_input_path(cls, *components):
        return os.path.join(cls.get_input_base_dir(), *components)
