import json
import os
import tempfile
import unittest
from abc import ABCMeta
from urllib.error import HTTPError

import httpretty

from ocdb.api.OCDBApi import OCDBApi, USER_DIR, new_api
from ocdb.configstore import MemConfigStore
from tests.helpers import ClientTest, TEST_URL, TEST_API_VERSION

TEST_DATA = """/begin_header
/identifier_product_doi=10.5067/SeaBASS/SCOTIA_PRINCE_FERRY/DATA001
/received=20040220
/affiliations=Bigelow_Laboratory_for_Ocean_Sciences
/investigators=William_Balch
/contact=bbalch@bigelow.org
/experiment=Scotia_Prince_ferry
/cruise=s030603w
/data_type=cast
/west_longitude=-66.4551[DEG]
/east_longitude=-66.4551[DEG]
/north_latitude=43.7621[DEG]
/south_latitude=43.7621[DEG]
/start_date=20030603
/end_date=20030603
/start_time=14:00:38[GMT]
/end_time=14:00:38[GMT]
/fields=date,time,lat,lon,depth,wt
/units=yyyymmdd,hh:mm:ss,degrees,degrees,meters,degreesc
/data_status=final
/delimiter=space
/documents=readme.txt
/data_file_name=T0_00686.EDF
/missing=-99.99
/water_depth=NA
/wind_speed=NA
/wave_height=NA
/secchi_depth=NA
/cloud_percent=NA
/station=NA
/calibration_files=no-calibration-file.txt
/end_header
20030603 14:00:38 43.7620 -66.4551 0.60 8.37
20030603 14:00:38 43.7620 -66.4551 1.30 7.05
"""

TEST_DATA_FILE_NAME = ""


class ApiTest(ClientTest, metaclass=ABCMeta):
    pass


class DatasetsApiTest(ApiTest):

    def test_upload_store_files(self):
        expected_response = {
            'chl-s170604w.sub': {'issues': [], 'status': 'OK'},
            'chl-s170710w.sub': {'issues': [], 'status': 'OK'}
        }

        url = TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/store/upload/submission"

        httpretty.register_uri(httpretty.POST,
                               url,
                               status=200,
                               body=json.dumps(expected_response).encode("utf-8"))
        dataset_paths = [self.get_input_path("chl", "chl-s170604w.sub"),
                         self.get_input_path("chl", "chl-s170710w.sub")]
        doc_file_paths = [self.get_input_path("cal_files", "ac90194.060328"),
                          self.get_input_path("cal_files", "DI7125f.cal"),
                          self.get_input_path("cal_files", "DI7125m.cal")]

        response = self.api.upload_submission(path="BIGELOW/BALCH/gnats", dataset_files=dataset_paths,
                                              doc_files=doc_file_paths, submission_id='test',
                                              publication_date='2020-01-01', allow_publication=False)
        self.assertIsInstance(response, dict)
        self.assertEqual(expected_response, response)

    def test_upload_store_files_without_docs(self):
        expected_response = {
            'chl-s170604w.sub': {'issues': [], 'status': 'OK'},
            'chl-s170710w.sub': {'issues': [], 'status': 'OK'}
        }

        url = TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/store/upload/submission"

        httpretty.register_uri(httpretty.POST,
                               url,
                               status=200,
                               body=json.dumps(expected_response).encode("utf-8"))
        dataset_paths = [self.get_input_path("chl", "chl-s170604w.sub"),
                         self.get_input_path("chl", "chl-s170710w.sub")]

        response = self.api.upload_submission(path="BIGELOW/BALCH/gnats", dataset_files=dataset_paths,
                                              submission_id='ohne docs',
                                              publication_date='2020-01-01', allow_publication=False)
        self.assertIsInstance(response, dict)
        self.assertEqual(expected_response, response)

    def test_upload_single_store_files(self):
        expected_response = {
            'chl-s170604w.sub': {'issues': [], 'status': 'OK'},
        }

        url = TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/store/upload/submission"

        httpretty.register_uri(httpretty.POST,
                               url,
                               status=200,
                               body=json.dumps(expected_response).encode("utf-8"))
        dataset_paths = self.get_input_path("chl", "chl-s170604w.sub")
        doc_file_paths = self.get_input_path("cal_files", "ac90194.060328")

        response = self.api.upload_submission(path="BIGELOW/BALCH/gnats", dataset_files=dataset_paths,
                                              doc_files=doc_file_paths, submission_id='test',
                                              publication_date='2020-01-01', allow_publication=False)
        self.assertIsInstance(response, dict)
        self.assertEqual(expected_response, response)

    def test_upload_store_file_with_none_pub_date(self):
        expected_response = {
            'chl-s170604w.sub': {'issues': [], 'status': 'OK'}
        }

        url = TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/store/upload/submission"

        httpretty.register_uri(httpretty.POST,
                               url,
                               status=200,
                               body=json.dumps(expected_response).encode("utf-8"))
        dataset_paths = self.get_input_path("chl", "chl-s170604w.sub")
        doc_file_paths = []

        response = self.api.upload_submission(path="BIGELOW/BALCH/gnats", dataset_files=dataset_paths,
                                              doc_files=doc_file_paths, submission_id='test',
                                              publication_date=None, allow_publication=False)
        self.assertIsInstance(response, dict)
        self.assertEqual(expected_response, response)

    def test_find_datasets(self):
        expected_response = {
            "totalCount": 2,
            "query": {"expr": "metadata.cruise:gnats"},
            "datasets": [
                {"id": "1", "path": "BIGELOW/BALCH/gnats", "name": "chl-s170604w.sub"},
                {"id": "2", "path": "BIGELOW/BALCH/gnats", "name": "chl-s170710w.sub"}
            ]
        }

        url = TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/datasets?expr=metadata.cruise%3Agnats&geojson=True"
        httpretty.register_uri(httpretty.GET,
                               url,
                               status=200,
                               body=json.dumps(expected_response).encode("utf-8"))
        response = self.api.find_datasets(expr="metadata.cruise:gnats")
        self.assertIsInstance(response, dict)
        self.assertEqual(expected_response, response)

    def test_validate_dataset(self):
        httpretty.register_uri(httpretty.POST,
                               TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/store/upload/submission/validate",
                               status=200)
        self.api.validate_submission_file(self.get_input_path("chl", "chl-s170604w.sub"))

    def test_add_datasets(self):
        httpretty.register_uri(httpretty.PUT,
                               TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/datasets",
                               status=200)
        self.api.add_dataset(self.get_input_path("chl", "chl-s170604w.sub"))

    def test_update_datasets(self):
        httpretty.register_uri(httpretty.POST,
                               TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/datasets",
                               status=200)
        self.api.update_dataset(self.get_input_path("chl", "chl-s170604w.sub"))

    def test_delete_datasets(self):
        httpretty.register_uri(httpretty.DELETE,
                               TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/datasets/3",
                               status=200)
        self.api.delete_dataset(dataset_id="3")

        # Force failure
        httpretty.register_uri(httpretty.DELETE,
                               TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/datasets/4",
                               status=404)
        with self.assertRaises(HTTPError):
            self.api.delete_dataset(dataset_id="4")

    def test_get_dataset(self):
        expected_response = {
            "id": "245",
            "name": "chl/chl-s170604w.sub",
            "metadata": {},
            "records": [[]]
        }
        httpretty.register_uri(httpretty.GET,
                               TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/datasets/245",
                               status=200,
                               body=json.dumps(expected_response).encode("utf-8"))
        response = self.api.get_dataset(dataset_id="245")
        self.assertIsInstance(response, dict)
        self.assertEqual(expected_response, response)

        # Force failure
        httpretty.register_uri(httpretty.GET,
                               TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/datasets/246",
                               status=404)
        with self.assertRaises(HTTPError):
            self.api.get_dataset(dataset_id="246")

    @unittest.skip('Not implemented')
    def test_get_dataset_by_name(self):
        expected_response = {
            "id": "245",
            "name": "chl/chl-s170604w.sub",
            "metadata": {},
            "records": [[]]
        }
        httpretty.register_uri(httpretty.GET,
                               TEST_URL + "/ocdb/api/" + TEST_API_VERSION
                               + "/datasets/BIGELOW/BALCH/gnats/chl/chl-s170604w.sub",
                               status=200,
                               body=json.dumps(expected_response).encode("utf-8"))
        response = self.api.get_dataset_by_name(dataset_path="BIGELOW/BALCH/gnats/chl/chl-s170604w.sub", fmt='json')
        self.assertIsInstance(response, dict)
        self.assertEqual(expected_response, response)

        # Force failure
        httpretty.register_uri(httpretty.GET,
                               TEST_URL + "/ocdb/api/" + TEST_API_VERSION
                               + "/datasets/BIGELOW/BALCH/gnats/chl/chl-s170604w.sub",
                               status=404)
        with self.assertRaises(HTTPError):
            self.api.get_dataset_by_name(dataset_path="BIGELOW/BALCH/gnats/chl/chl-s170604w.sub")

        with self.assertRaises(ValueError) as cm:
            self.api.get_dataset_by_name(dataset_path="BIGELOW/gnats/chl-s170604w.sub")
        self.assertEqual("Invalid dataset path, must have format affil/project/cruise/name,"
                         " but was BIGELOW/gnats/chl-s170604w.sub", f"{cm.exception}")

        with self.assertRaises(ValueError) as cm:
            self.api.get_dataset_by_name(dataset_path="BIGELOW/BALCH//chl/chl-s170604w.sub")
        self.assertEqual("Invalid dataset path: BIGELOW/BALCH//chl/chl-s170604w.sub", f"{cm.exception}")

    def test_list_datasets_in_path(self):
        expected_response = [
            {
                "id": "242",
                "name": "chl/chl-s170610w.sub",
                "metadata": {},
                "records": [[]]
            },
            {
                "id": "245",
                "name": "chl/chl-s170604w.sub",
                "metadata": {},
                "records": [[]]
            }
        ]
        httpretty.register_uri(httpretty.GET,
                               TEST_URL + "/ocdb/api/" + TEST_API_VERSION
                               + "/datasets/BIGELOW/BALCH/gnats",
                               status=200,
                               body=json.dumps(expected_response).encode("utf-8"))
        response = self.api.list_datasets_in_path(dataset_path="BIGELOW/BALCH/gnats")
        self.assertIsInstance(response, list)
        self.assertEqual(expected_response, response)

        # Force failure
        httpretty.register_uri(httpretty.GET,
                               TEST_URL + "/ocdb/api/" + TEST_API_VERSION
                               + "/datasets/IGELOW/ELCH/gnitz",
                               status=404)
        with self.assertRaises(HTTPError):
            self.api.list_datasets_in_path(dataset_path="IGELOW/ELCH/gnitz")

        with self.assertRaises(ValueError):
            self.api.list_datasets_in_path(dataset_path="BIGELOW/BALCH/gnats/gnark")

        with self.assertRaises(ValueError):
            self.api.list_datasets_in_path(dataset_path="BIGELOW/BALCH")


class ConfigApiTest(ApiTest):
    def test_set_get_config_value(self):
        with self.assertRaises(ValueError) as cm:
            self.api.set_config_param("bibo", 132)
        self.assertEqual('unknown configuration parameter "bibo"', f'{cm.exception}')

        self.api.set_config_param("server_url", 'http://bibo')
        self.assertEqual('http://bibo', self.api.get_config_param("server_url"))

    def test_server_url(self):
        with self.assertRaises(ValueError) as cm:
            self.api.server_url = None
        self.assertEqual('"server_url" must be specified', f'{cm.exception}')

        server_url = 'http://test:18432'
        self.api.server_url = server_url
        self.assertEqual(server_url, self.api.server_url)
        self.assertEqual(server_url, self.api.get_config_param('server_url'))

    def test_api_with_defaults(self):
        api_with_defaults = OCDBApi()
        self.assertIsNotNone(api_with_defaults.config)
        self.assertTrue(api_with_defaults.server_url is None
                        or api_with_defaults.server_url is not None)

    def test_make_url(self):
        api = OCDBApi(config_store=MemConfigStore())
        with self.assertRaises(ValueError) as cm:
            api._make_url('/datasets')
        self.assertEqual('"server_url" is not configured', f'{cm.exception}')

        server_url_with_trailing_slash = 'http://localhost:2385/'
        api = OCDBApi(config_store=MemConfigStore(server_url=server_url_with_trailing_slash))
        self.assertEqual('http://localhost:2385/ocdb/api/' + TEST_API_VERSION + '/datasets', api._make_url('datasets'))
        self.assertEqual('http://localhost:2385/ocdb/api/' + TEST_API_VERSION + '/datasets', api._make_url('/datasets'))

        server_url_without_trailing_slash = 'http://localhost:2385'
        api = OCDBApi(config_store=MemConfigStore(server_url=server_url_without_trailing_slash))
        self.assertEqual('http://localhost:2385/ocdb/api/' + TEST_API_VERSION + '/datasets', api._make_url('datasets'))
        self.assertEqual('http://localhost:2385/ocdb/api/' + TEST_API_VERSION + '/datasets', api._make_url('/datasets'))


class OCDBApi_update_user_Tests(unittest.TestCase):

    def setUp(self) -> None:
        self.api = OCDBApi(server_url="https://bibosrv", config_store=MemConfigStore(server_url="https://bertsrv"))

    def test__update_user__changing_the_password_is_not_allowed(self):
        result = self.api.update_user(username='sabine', key='password', value='someone23')
        expected = {'message': "Please use '$ocdb-cli user pwd <user>' instead of '$ocdb-cli user "
                               "update' for changing the password of a user."}
        self.assertEqual(result, expected)

    def test__update_user__changing_the_id_is_not_allowed(self):
        result = self.api.update_user(username='sabine', key='id', value='23')
        expected = {
            'message': 'Changing the field "id" of an user is not allowed.'
        }
        self.assertEqual(result, expected)

    def test__update_user__changing_the_name_is_not_allowed(self):
        result = self.api.update_user(username='sabine', key='name', value='new_name')
        expected = {
            'message': 'Changing the field "name" of an user is not allowed.'
        }
        self.assertEqual(result, expected)


class ApiImplTest(ApiTest):

    def setUp(self):
        login_info_file = os.path.join(USER_DIR, "login_info")
        if os.path.isfile(login_info_file):
            os.remove(login_info_file)

        fp = tempfile.NamedTemporaryFile(delete=False, suffix='.sb', mode='w')
        fp.write(TEST_DATA)
        global TEST_DATA_FILE_NAME
        TEST_DATA_FILE_NAME = fp.name
        fp.close()

    def test_constr(self):
        api = OCDBApi()
        self.assertIsNotNone(api.config)
        # Don't understand
        # self.assertIsNone(api.server_url)

        api = OCDBApi(server_url="https://bibosrv", config_store=MemConfigStore(server_url="https://bertsrv"))
        self.assertIsNotNone(api.config)
        self.assertEqual("https://bibosrv", api.server_url)

    def test_store_and_load_login_cookie(self):
        cookie_content = "nasenmann.org; expires: never"
        OCDBApi.store_login_cookie(cookie_content)

        result = OCDBApi.read_login_cookie()
        self.assertEqual(cookie_content, result)

    def test_load_login_cookie_not_existing(self):
        result = OCDBApi.read_login_cookie()
        self.assertIsNone(result)

    def test_store_twice_overrides_cookie_file(self):
        cookie_content = "nasenmann.org; expires: never"
        OCDBApi.store_login_cookie(cookie_content)

        cookie_content = "hell-yeah!; expires: now"
        OCDBApi.store_login_cookie(cookie_content)

        result = OCDBApi.read_login_cookie()
        self.assertEqual(cookie_content, result)

    def test_delete_login_cookie(self):
        cookie_content = "nasenmann.org; expires: never"
        OCDBApi.store_login_cookie(cookie_content)

        login_info_file = os.path.join(USER_DIR, "login_info")
        self.assertTrue(os.path.isfile(login_info_file))

        OCDBApi.delete_login_cookie()
        self.assertFalse(os.path.isfile(login_info_file))

    def test_add_submission_file(self):
        api = new_api()
        result = api.add_submission_file(submission_id='test', file_name=TEST_DATA_FILE_NAME, typ="dfsvdfsv")
        expected = {"message": "Type must be MEASUREMENT or DOCUMENT"}
        self.assertEqual(expected, result)


class ApiUserTest(ApiTest):
    def test_user_add(self):
        expected_response = {
            "username": "admin",
            "first_name": "Submit",
            "last_name": "Submit",
            "password": "admin",
            "email": "jj",
            "phone": "hh",
            "roles": [
                "admin"
            ],
        }

        url = TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/users"
        httpretty.register_uri(httpretty.POST,
                               url,
                               status=200,
                               body=json.dumps(expected_response).encode("utf-8"))

        response = self.api.add_user(**expected_response)
        self.assertIsInstance(response, dict)
        self.assertEqual(expected_response, response)
        res = self.api.get_config_param('password-salt')
        self.assertIsNone(res)

    def test_change_user_login(self):
        url = TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/users/login"
        httpretty.register_uri(httpretty.PUT,
                               url,
                               status=200,
                               json={})
        url = TEST_URL + "/ocdb/api/" + TEST_API_VERSION + "/users/login"
        httpretty.register_uri(httpretty.GET, url, status=200, body=json.dumps('helge').encode('utf-8'))

        # Test user get initial password by admin
        self.api.set_config_param('password-salt', None)

        self.api.change_user_login('helge2', 'passwd1', 'passwd2')
        res = self.api.get_config_param('password-salt')
        self.assertIsNone(res)

        # Check whether the client creates a salt when the user changes own password
        self.api.change_user_login('helge', 'passwd1', 'passwd2')
