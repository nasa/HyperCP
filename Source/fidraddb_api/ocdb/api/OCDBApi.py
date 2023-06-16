import ssl
import sys
import pathlib
import json
import os
import shutil
import urllib.parse
import urllib.request
import zipfile
from typing import Any, Optional, Sequence, List, Union

import pandas as pd
from httpretty.http import HttpBaseClass

from . import utils
from .api import Api, Config, JsonObj
from .mpf import MultiPartForm
from ..configstore import ConfigStore, JsonConfigStore
from ..version import NAME, VERSION, DESCRIPTION, API_VERSION_TAG
#from ocdb.api.util import DATASET_TYPES

USER_AGENT = f"{NAME} / {VERSION} {DESCRIPTION}"

API_PATH_PREFIX = "/ocdb/api/" + API_VERSION_TAG

USER_DIR = os.path.expanduser(os.path.join('~', '.ocdb'))
DEFAULT_CONFIG_FILE_NAME = 'ocdb-client.json'
DEFAULT_CONFIG_FILE = os.path.join(USER_DIR, DEFAULT_CONFIG_FILE_NAME)

VALID_CONFIG_PARAM_NAMES = {'server_url', 'traceback', 'password-salt'}


def new_api(config_store: ConfigStore = None, server_url: str = None) -> Api:
    """Factory that creates a new API instance."""
    return OCDBApi(config_store=config_store, server_url=server_url)


def _ensure_sequence(obj) -> Sequence[str]:
    if not obj:
        return []
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
        return obj
    else:
        return [obj]


class _DefaultConfigStore(JsonConfigStore):

    def __init__(self):
        super().__init__(DEFAULT_CONFIG_FILE)


class OCDBApi(Api):

    def __init__(self,
                 config_store: ConfigStore = None,
                 server_url: str = None):
        if config_store is None:
            config_store = _DefaultConfigStore()
        self._config_store = config_store
        self._config = None
        if server_url is not None:
            self.server_url = server_url

        traceback = self.get_config_param('traceback')
        if traceback is not None:
            sys.tracebacklimit = int(traceback)

        self.verbose = False

    # Remote dataset access

    def fidrad_upload(self, cal_char_files: Union[str, Sequence[str]],
                      disagree_publication: bool) -> JsonObj:
        """
        Generate a submission by uploading Cal/Char files to the data store.
        :param cal_char_files: A list of calibration or characterisation files
        :param disagree_publication: True or False
        :return: A message from the server
        """
        cal_char_files = _ensure_sequence(cal_char_files)

        form = MultiPartForm()
        form.add_field('disagree_publication', str(disagree_publication))

        for cal_char_file in cal_char_files:
            form.add_file(f'cal_char_files', os.path.basename(cal_char_file), cal_char_file, mime_type="text/plain")

        data = bytes(form)

        request = self._make_request('/store/FidRadDB/upload/cal_char', data=data, method=form.method)
        request.add_header('Content-type', form.content_type)
        request.add_header('Content-length', f'{len(data)}')
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def fidrad_history_tail(self, num_lines: int) -> JsonObj:
        """
        Get the tail of the FidRadDb history with the user defined number of lines
        :param num_lines: The number of lines
        :return: A JSON object representing the history tail
        """
        request = self._make_request(f'/store/FidRadDB/history/tail/{num_lines}', method=HttpBaseClass.GET)
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def fidrad_history_search(self, search_string: str, max_num_lines: int) -> JsonObj:
        """
        Returns a grep-like but bottom-up search result from the FidRadDB history file with a user-defined maximum
        number of result lines.
        :param search_string: The string to be searched for in the history.
        :param max_num_lines: The maximum number of search results.
        """
        quoted_search = urllib.parse.quote(search_string)
        request = self._make_request(f'/store/FidRadDB/history/search/{quoted_search}/{max_num_lines}', method=HttpBaseClass.GET)
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def fidrad_list_files(self, name_part: str) -> JsonObj:
        """
        Lists the files available on the server. If a name-part is specified, only files containing this part are
        returned.
        """
        quoted_name_part = urllib.parse.quote(name_part)
        request = self._make_request(f'/store/FidRadDB/list/files/{quoted_name_part}', method=HttpBaseClass.GET)
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def fidrad_delete_file(self, file_name: str) -> JsonObj:
        """
        Deletes the requested file.
        """
        quoted_filename = urllib.parse.quote(file_name)
        request = self._make_request(f'/store/FidRadDB/delete/file/{quoted_filename}', method=HttpBaseClass.DELETE)
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def fidrad_download_file(self, file_name: str, output_dir: str) -> str:
        """
          Download a FidRadDB Cal/Char file with the user defined file_name to a user defined output directory.
          :param file_name: The file_name to download from server.
          :param output_dir: An output dir path.
          :return: A message
          """
        quoted_filename = urllib.parse.quote(file_name)
        request = self._make_request(f'/store/FidRadDB/download/file/{quoted_filename}', method=HttpBaseClass.GET)
        message = ""

        if not output_dir:
            output_dir = '.'

        if not os.path.isabs(output_dir):
            if not output_dir.startswith("."):
                output_dir = os.path.join('.', output_dir)
        else:
            if os.path.isfile(output_dir):
                return f"Unable to write file to '{output_dir}' because output_dir is an existing file."

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with urllib.request.urlopen(request) as response:
            out_file_path = os.path.join(output_dir, file_name)
            try:
                with open(out_file_path, 'wb') as f:
                    shutil.copyfileobj(response, f)
            except Exception as e:
                message = f"Exception occurs while trying to write file to '{out_file_path}'. Exception: {repr(e)}"
            else:
                message += f'File successfully written to {out_file_path}'
        return message

    def upload_submission(self, path: str, dataset_files: Union[str, Sequence[str]],
                          submission_id: str, doc_files: Optional[Union[str, Sequence[str]]] = None,
                          publication_date: Optional[str] = None,
                          allow_publication: Optional[bool] = False) -> JsonObj:
        """
        Generate a submission by uploading database and files to the submission database
        :param path: The path to the store. Should be of format affiliation/cruise/experiment
        :param dataset_files: A list of dataset file names
        :param doc_files: A list of document file names
        :param submission_id: Q unique submission ID
        :param publication_date: The date the data is to be published
        :param allow_publication: Allow publication?
        :return: A message from the server
        """

        dataset_files = _ensure_sequence(dataset_files)
        doc_files = _ensure_sequence(doc_files)

        form = MultiPartForm()
        form.add_field('path', path)
        form.add_field('submissionid', submission_id)

        form.add_field('publicationdate', str(publication_date))
        form.add_field('allowpublication', str(allow_publication))

        for dataset_file in dataset_files:
            form.add_file(f'datasetfiles', os.path.basename(dataset_file), dataset_file, mime_type="text/plain")
        for doc_file in doc_files:
            form.add_file(f'docfiles', os.path.basename(doc_file), doc_file)

        # print(str(form))
        data = bytes(form)

        request = self._make_request('/store/upload/submission', data=data, method=form.method)
        request.add_header('Content-type', form.content_type)
        request.add_header('Content-length', f'{len(data)}')
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def download_datasets_by_ids(self, ids: List[str], download_docs: bool, out_fn: Optional[str]) -> str:
        """
        Download dataset files by dataset IDs
        :param ids: A list of dataset IDs
        :param download_docs: Whether document files shall be downloaded as well
        :param out_fn: A filename for the resulting zip file.
        :return: A message where the files have been stored
        """

        message = ""

        data = {'id_list': ids, 'docs': download_docs}
        data = json.dumps(data).encode('utf-8')

        request = self._make_request(f'/store/download', data=data, method="POST")

        if not out_fn:
            out_fn = 'download.zip'
        else:
            if pathlib.Path(out_fn).suffix != ".zip":
                out_fn += ".zip"
                message += "Output file must be zip. Added extension .zip"

        with urllib.request.urlopen(request) as response, open(out_fn, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            out_file.close()
            with zipfile.ZipFile(out_fn) as zf:
                zf.extractall()

        message += f'{ids} downloaded to {out_fn}'
        return message

    def add_dataset(self, dataset_file: str):
        """
        Add a dataset file to the Submission Database
        :param dataset_file: The dataset file to be added
        :return: A message from the server
        """
        with open(dataset_file) as fp:
            dataset_json = fp.read()
        request = self._make_request('/datasets', method="PUT", data=dataset_json.encode("utf-8"))
        with urllib.request.urlopen(request) as response:
            return response.read()

    def update_dataset(self, dataset_file: str):
        with open(dataset_file) as fp:
            dataset_json = fp.read()
        request = self._make_request(f'/datasets', method="POST", data=dataset_json.encode("utf-8"))
        with urllib.request.urlopen(request) as response:
            return response.read()

    def delete_dataset(self, dataset_id: str):
        request = self._make_request(f'/datasets/{dataset_id}', method="DELETE")
        with urllib.request.urlopen(request) as response:
            return response.read()

    def delete_datasets_by_submission(self, submission_id: str):
        """
        Remove all data from the search database linked to a submission.
        :param submission_id: The ID of the submission
        :return: A message from the server
        """
        request = self._make_request(f'/datasets/submission/{submission_id}', method="DELETE")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def get_datasets_by_submission(self, submission_id: str):
        """
        Get all data from the search database linked to a submission.
        :param submission_id: The ID of the submission
        :return: A message from the server
        """
        request = self._make_request(f'/datasets/submission/{submission_id}', method="GET")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    @staticmethod
    def _make_pandas_from_dataset(ds: JsonObj) -> pd.DataFrame:
        df = pd.DataFrame(ds['records'])
        df.columns = ds['attributes']
        return df

    def get_dataset(self, dataset_id: str, fmt: str = 'json') -> Union[JsonObj, pd.DataFrame]:
        """
        Get a dataset from the Search Database by dataset ID.
        :param dataset_id: ID of teh dataset
        :param fmt: return format. Can be 'pandas' or 'json'
        :return:
        """
        request = self._make_request(f'/datasets/{dataset_id}', method="GET")
        with urllib.request.urlopen(request) as response:
            js = json.load(response)
            if fmt == 'pandas':
                return OCDBApi._make_pandas_from_dataset(js)
            else:
                return js

    def get_dataset_by_name(self, dataset_path: str, fmt: str) -> Union[JsonObj, pd.DataFrame]:
        path_components = _split_dataset_path(dataset_path)
        if len(path_components) < 4:
            raise ValueError("Invalid dataset path, "
                             f"must have format affil/project/cruise/name, but was {dataset_path}")
        affil = path_components[0]
        project = path_components[1]
        cruise = path_components[2]
        name = "/".join(path_components[3:])
        request = self._make_request(f'/datasets/{affil}/{project}/{cruise}/{name}', method="GET")
        with urllib.request.urlopen(request) as response:
            js = json.load(response)
            if format == 'pandas':
                return OCDBApi._make_pandas_from_dataset(js)
            else:
                return json.load(response)

    def list_datasets_in_path(self, dataset_path: str) -> JsonObj:
        try:
            affil, project, cruise = _split_dataset_path(dataset_path)
        except ValueError as e:
            raise ValueError(f"Invalid dataset path, "
                             f"must have format affil/project/cruise, but was {dataset_path}") from e
        request = self._make_request(f'/datasets/{affil}/{project}/{cruise}', method="GET")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def find_datasets(self, **kwargs) -> JsonObj:
        """
        Search datasets by expression.

        :param kwargs:
        :return: A JSON object containing a list of datasets found in the search database
        """
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        kwargs['geojson'] = True
        params = urllib.parse.urlencode(kwargs)
        request = self._make_request(f'/datasets?{params}', method="GET")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def get_submission(self, submission_id: str) -> JsonObj:
        """
        Get a submission by the user defined ID
        :param submission_id: The submission ID
        :return: A JSON object representing the submission
        """
        request = self._make_request(f'/store/upload/submission/{submission_id}', method="GET")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def get_submissions_for_user(self, user_name: Optional[str]) -> JsonObj:
        """
        Get all submission for a user
        :param user_name: User Name
        :return: A JSON object representing the resulting list of submissions
        """

        path = '/store/upload/user'
        if user_name:
            path = f'/store/upload/user/{user_name}'

        request = self._make_request(path, method="GET")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def update_submission_status(self, submission_id: str, status: str) -> JsonObj:
        """
        Change the status of a submission
        :param submission_id: The user defined ID of a submission
        :param status: The new status
        :return: A message from the server
        """
        # Should we change the code to:
        # 1. data = {'status': status, 'date': None} oder
        # 2. data = {'status': status}
        # 3. data = {'status': status, 'date': current_publication_date}    # Current publication date of existing submission could be None.
        # However, Sabine, please check whether key 'date' is correct for 'publication_date' (see _extract_date() in _handlers.py)
        data = {'status': status}
        data = json.dumps(data).encode('utf-8')

        request = self._make_request(f'/store/status/submission/{submission_id}', data=data, method="PUT")
        request.add_header('Content-Type', 'application/json')

        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def delete_submission(self, submission_id: str) -> JsonObj:
        """
        Delete a submission by the user defined ID
        :param submission_id: Submission ID
        :return: A message from the server
        """
        request = self._make_request(f'/store/upload/submission/{submission_id}', method="DELETE")

        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def download_submission_file(self, submission_id: str, index: int, out_fn: Optional[str]) -> str:
        """
        Download a Submission File by user defined submission ID and the index of the file
        :param submission_id: The submission ID
        :param index: The index of the file
        :param out_fn: An output file name
        :return: A message
        """
        request = self._make_request(f'/store/download/submissionfile/{submission_id}/{index}', method="GET")
        message = ""

        if not out_fn:
            out_fn = 'download.zip'
        else:
            if pathlib.Path(out_fn).suffix != ".zip":
                out_fn += ".zip"
                message += "Output file must be zip. Added extension .zip"

        with urllib.request.urlopen(request) as response, open(out_fn, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            out_file.close()
            with zipfile.ZipFile(out_fn) as zf:
                zf.extractall()
        message += f'{submission_id}/{index} downloaded to {out_fn}'
        return message

    def get_submission_file(self, submission_id: str, index: int) -> JsonObj:
        request = self._make_request(f'/store/upload/submissionfile/{submission_id}/{index}', method="GET")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def delete_submission_file(self, **kwargs) -> JsonObj:
        """
        Delete a submission File
        :param kwargs:
        :return:
        """
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        params = urllib.parse.urlencode(kwargs)
        request = self._make_request(f'/submission?{params}', method="GET")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def update_submission_file(self, submission_id: str, file_name: str, index: int) -> JsonObj:
        """
        Upload a submission file by user defined Submission ID and index
        :param submission_id: Submission ID
        :param index: Submission File index
        :param file_name: The file name to be uploaded
        :return: A message from the server
        """
        form = MultiPartForm()

        form.add_file(f'files', os.path.basename(file_name), file_name, mime_type="text/plain")

        data = bytes(form)

        request = self._make_request(f'/store/upload/submissionfile/{submission_id}/{index}',
                                     data=data,
                                     method="PUT")

        request.add_header('Content-type', form.content_type)
        request.add_header('Content-length', f'{len(data)}')

        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def add_submission_file(self, submission_id: str, file_name: str, typ: str) -> Union[JsonObj, str]:
        """
        Upload a submission file by user defined Submission ID and index
        :param typ: Type of upload [MEASUREMENT | DOCUMENT]
        :param submission_id: Submission ID
        :param file_name: The file name to be uploaded
        :return: A message from the server
        """
        form = MultiPartForm()

        if typ not in DATASET_TYPES:
            return {"message": "Type must be MEASUREMENT or DOCUMENT"}

        form.add_file(f'files', os.path.basename(file_name), file_name, mime_type="text/plain")

        data = bytes(form)

        request = self._make_request(f'/store/add/submissionfile/{submission_id}/{typ}',
                                     data=data,
                                     method="POST")

        request.add_header('Content-type', form.content_type)
        request.add_header('Content-length', f'{len(data)}')

        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def validate_submission_file(self, file_name: str) -> JsonObj:
        """
        Validate a dataset
        :param file_name:The dataset file to be validated
        :return: The result of the validation
        """
        with open(file_name) as fp:
            dataset_json = fp.read()

        send = {'data': dataset_json}

        request = self._make_request('/store/upload/submission/validate', method="POST",
                                     data=json.dumps(send).encode('utf-8'))
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def add_user(self, username: str, password: str, email: str, roles: Sequence[str], first_name: str = '',
                 last_name: str = '', phone: str = '') -> JsonObj:
        """
        Add a user to the OCDB database system.
        :param username: The user name
        :param password: A password
        :param first_name: The First Name of the User
        :param last_name: The last name of the User
        :param email: The email of the user
        :param phone: The phone number
        :param roles: A list of roles
        :return: A message from the server
        """

        password = utils.encrypt(password)

        data = {
            'name': username,
            'first_name': first_name,
            'last_name': last_name,
            'password': password,
            'email': email,
            'phone': phone,
            'roles': roles
        }
        data = json.dumps(data).encode('utf-8')

        request = self._make_request(f'/users', data=data, method="POST")
        request.add_header('Content-Type', 'application/json')

        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def delete_user(self, username: str) -> JsonObj:
        """
        delete a user
        :param username: The user name to be deleted
        :return: A message from  the server
        """
        request = self._make_request(f'/users/{username}', method="DELETE")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def update_user(self, username: str, key: str, value: str) -> JsonObj:
        """
        Update user info
        :param username: The user name
        :param key: The field to be updated
        :param value: The value the field is to be updated by
        :return: A message from the server
        """
        if key == 'password':
            return {
                'message': 'Please use \'$ocdb-cli user pwd <user>\' instead of \'$ocdb-cli user update\' for'
                           ' changing the password of a user.'
            }

        if not (key in ['first_name', 'last_name', 'email', 'phone', 'roles']):
            return {
                'message': f'Changing the field "{key}" of an user is not allowed.'
            }

        user = self.get_user(username)

        user[key] = value

        data = json.dumps(user).encode('utf-8')
        request = self._make_request(f'/users/{username}', data=data, method="PUT")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def change_user_login(self, username: str, password: str, new_password: str) -> JsonObj:
        """
        Update user info
        :param new_password: New Password
        :param password: Old Password if user changes own password
        :param username: The username if admin changes for another user
        :return: A message from the server
        """

        password = utils.encrypt(password)

        new_password = utils.encrypt(new_password)

        # Admin does not have to state oldpassword, to change pwd of other users!
        data = json.dumps({'username': username, 'oldpassword': password, 'newpassword1': new_password,
                           'newpassword2': new_password}).encode('utf-8')

        request = self._make_request(f'/users/login', data=data, method="PUT")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def get_user(self, username: str) -> JsonObj:
        """
        Get info for a user
        :param username: User name
        :return: A JSON representation of the user
        """
        request = self._make_request(f'/users/{username}', method="GET")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def whoami(self) -> JsonObj:
        """
        Who am I
        :return: The user name
        """
        request = self._make_request(f'/users/login', method="GET")

        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def list_user(self) -> JsonObj:
        """
        List user names
        :return: The user name list
        """
        request = self._make_request(f'/users', method="GET")
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def login_user(self, username: Optional[str], password: Optional[str]) -> JsonObj:
        """
        Login to the OCDB database system
        :param username: User name
        :param password: Password
        :return: A JSON representation of the user
        """

        password = utils.encrypt(password)

        data = {'username': username, 'password': password, 'client_version': VERSION, 'client': 'cli'}
        data = json.dumps(data).encode('utf-8')

        request = self._make_request(f'/users/login', data=data, method="POST")
        try:
            with urllib.request.urlopen(request) as response:
                info = response.info()
                if info.__contains__("Set-Cookie"):
                    cookie = info.__getitem__("Set-Cookie")
                    OCDBApi.store_login_cookie(cookie)

                return json.load(response)
        except Exception as e:
            raise ValueError(str(e))

    def logout_user(self) -> JsonObj:
        """
        Logout from teh OCDB database system
        :return: A message from the server
        """
        cookie = OCDBApi.read_login_cookie()
        if cookie is None:
            pass

        request = self._make_request(f'/users/logout', method="GET")

        # Should be a message in the headers, but I can't find it tb 2019-04-29
        OCDBApi.delete_login_cookie()
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    # Local configuration access
    def version(self):
        from ocdb.version import VERSION

        return {"ocdb-cli version": VERSION}

    # Local configuration access
    def info(self):
        from ocdb.version import VERSION, DESCRIPTION, NAME, LICENSE_TEXT, DOCS_URL

        return {"Name": NAME, "Version": VERSION, "API Version": API_VERSION_TAG, "Description": DESCRIPTION, "Docs": DOCS_URL, "License": LICENSE_TEXT}

    @property
    def config(self) -> Config:
        """ Return a copy of the current API configuration. """
        self._ensure_config_initialized()
        return dict(self._config)

    def get_config_param(self, name: str, default: Any = None) -> Optional[Any]:
        """ Get the value of configuration parameter with given *name*. """
        self._ensure_config_initialized()

        return self._config.get(name, default)

    def set_config_param(self, name: str, value: Optional[Any], write: bool = False):
        """ Set the value of configuration parameter with given *name* to *value*. """
        self._ensure_valid_config_name(name)
        self._ensure_config_initialized()
        self._config[name] = value
        if write:
            self._config_store.write(self._config)

    @property
    def server_url(self) -> Optional[str]:
        """ Get the current value of the server URL. May be None, if not configured yet. """
        return self.get_config_param('server_url', None)

    @server_url.setter
    def server_url(self, server_url: str):
        """ Set the the server URL to *server_url*. """
        if not server_url:
            raise ValueError('"server_url" must be specified')
        self.set_config_param('server_url', server_url)

    # Implementation helpers

    def _make_request(self, path: str, method=None, data=None, headers=None) -> urllib.request.Request:
        url = self._make_url(path)
        if headers is None:
            headers = {}

        cookie = OCDBApi.read_login_cookie()
        if cookie is not None:
            headers.update({"Cookie": cookie})

        if self.verbose:
            print('Connecting to', url)

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        request.add_header("User-Agent", USER_AGENT)
        return request

    def _make_url(self, path: str):
        url = self.server_url
        if not url:
            raise ValueError('"server_url" is not configured')
        if url.endswith('/'):
            url = url[0: -1]
        if not path.startswith('/'):
            path = '/' + path
        return url + API_PATH_PREFIX + path

    @classmethod
    def _ensure_valid_config_name(cls, name: str):
        if name not in VALID_CONFIG_PARAM_NAMES:
            raise ValueError(f'unknown configuration parameter "{name}"')

    def _ensure_config_initialized(self):
        if self._config is None:
            config = self._config_store.read()
            for name in config:
                self._ensure_valid_config_name(name)
            self._config = config

    @staticmethod
    def store_login_cookie(cookie: str):
        login_info_file = os.path.join(USER_DIR, "login_info")
        if os.path.isfile(login_info_file):
            os.remove(login_info_file)

        with open(login_info_file, "w") as out_file:
            out_file.write(cookie)

    @staticmethod
    def read_login_cookie() -> Optional[str]:
        login_info_file = os.path.join(USER_DIR, "login_info")
        if os.path.isfile(login_info_file):
            with open(login_info_file, "r") as in_file:
                return in_file.read()

        return None

    @staticmethod
    def delete_login_cookie():
        login_info_file = os.path.join(USER_DIR, "login_info")
        if os.path.isfile(login_info_file):
            os.remove(login_info_file)


def _split_dataset_path(dataset_path: str) -> Sequence[str]:
    path_components = dataset_path.split('/')
    for path_component in path_components:
        if path_component.strip() == "":
            raise ValueError(f"Invalid dataset path: {dataset_path}")
    return path_components
