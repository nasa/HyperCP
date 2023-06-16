from abc import ABCMeta, abstractmethod
from typing import Dict, Any, Optional, Sequence, Union, List
import pandas as pd

UNDEFINED = object()

Config = Dict[str, Any]

JsonObj = Union[Dict, List]


class Api(metaclass=ABCMeta):

    # Remote dataset access

    @abstractmethod
    def fidrad_upload(self, cal_char_files: Union[str, Sequence[str]],
                      disagree_publication: bool) -> JsonObj:
        """Upload the given Cal/Char files and return a validation report for each file."""

    @abstractmethod
    def fidrad_history_tail(self, num_lines: int) -> JsonObj:
        """Returns the tail of the FidRadDB history file with a user defined maximum number of lines."""

    @abstractmethod
    def fidrad_history_search(self, search_string: str, max_num_lines: int) -> JsonObj:
        """
        Returns a grep like bottom up search result from the FidRadDB history file with
        a user defined maximum number of lines.
        """

    @abstractmethod
    def fidrad_list_files(self, name_part: str) -> JsonObj:
        """
        Lists the files available on the server. If a name-part is specified, only files containing this part are
        returned.
        """

    @abstractmethod
    def fidrad_delete_file(self, file_name: str) -> JsonObj:
        """
        Deletes the requested file.
        """

    def fidrad_download_file(self, file_name: str, output_dir: str) -> str:
        """
          Download a FidRadDB Cal/Char file with the user defined file_name to a user defined output directory.
          :param file_name: The file_name to download from server.
          :param output_dir: An output dir path.
          :return: A message
          """

    @abstractmethod
    def upload_submission(self, path: str, dataset_files: Union[str, Sequence[str]],
                          doc_files: Optional[Union[str, Sequence[str]]],
                          submission_id: str, publication_date: str, allow_publication: bool) -> JsonObj:
        """Upload the given dataset and doc files and return a validation report for each dataset file."""

    @abstractmethod
    def validate_submission_file(self, file_name: str) -> JsonObj:
        """Validate the given dataset and return a validation report."""

    @abstractmethod
    def delete_dataset(self, dataset_file: str):
        """Delete a dataset."""

    @abstractmethod
    def get_datasets_by_submission(self, submission_id: str):
        """Get datasets by submission ID"""

    @abstractmethod
    def delete_datasets_by_submission(self, submission_id: str):
        """Delete datasets by submission ID"""

    @abstractmethod
    def find_datasets(self,
                      expr: str = None,
                      offset: int = 1,
                      count: int = 1000) -> JsonObj:
        """Find datasets."""

    @abstractmethod
    def get_dataset(self, dataset_id: str, fmt: str) -> Union[JsonObj, pd.DataFrame]:
        """Get dataset by ID."""

    @abstractmethod
    def get_dataset_by_name(self, dataset_path: str, fmt: str) -> Union[JsonObj, pd.DataFrame]:
        """Get dataset by path and name."""

    @abstractmethod
    def list_datasets_in_path(self, dataset_path: str) -> JsonObj:
        """List datasets in path."""

    # Submission Management

    @abstractmethod
    def get_submission(self, submission_id: str) -> JsonObj:
        """Get submission"""

    @abstractmethod
    def update_submission_status(self, submission_id: str, status: str) -> JsonObj:
        """Get submission"""

    @abstractmethod
    def get_submissions_for_user(self, user_name: Optional[str]) -> JsonObj:
        """Get submissions for user"""

    @abstractmethod
    def delete_submission(self, submission_id: str) -> JsonObj:
        """Delete submission"""

    @abstractmethod
    def download_submission_file(self, submission_id: str, index: int, out_fn: Optional[str]) -> JsonObj:
        """Download submission file by submission id and index"""

    @abstractmethod
    def get_submission_file(self, submission_id: str, index: int) -> JsonObj:
        """Get submission file by submission id and index"""

    @abstractmethod
    def update_submission_file(self, **kwargs) -> JsonObj:
        """Re-upload a single suibmission file"""

    @abstractmethod
    def add_submission_file(self, **kwargs) -> JsonObj:
        """Add a single suibmission file"""

    @abstractmethod
    def delete_submission_file(self, **kwargs) -> JsonObj:
        """Delete s submission file by sbmission Id and index"""

    # User management

    @abstractmethod
    def add_user(self, username: str,  password: str, first_name: str, last_name: str, email: str, phone: str,
                 roles: Sequence[str]) -> JsonObj:
        """Add a new user"""

    @abstractmethod
    def delete_user(self, name: str) -> JsonObj:
        """Delete existing user"""

    @abstractmethod
    def update_user(self, name: str, key: str, value: str) -> JsonObj:
        """Update user Info"""

    @abstractmethod
    def get_user(self, name: str) -> JsonObj:
        """Get user info by user name"""

    @abstractmethod
    def change_user_login(self, username: str, password: str, new_password: str) -> JsonObj:
        """Change user login (password)"""

    @abstractmethod
    def login_user(self, username: Optional[str], password: Optional[str]) -> JsonObj:
        """Log in with username and password"""

    # Local configuration access

    @property
    @abstractmethod
    def config(self) -> Config:
        """ Return a copy of the current API configuration. """

    @abstractmethod
    def get_config_param(self, name: str, default: Any = None) -> Optional[Any]:
        """ Get the value of configuration parameter with given *name*. """

    @abstractmethod
    def set_config_param(self, name: str, value: Optional[Any], write: bool = False):
        """ Set the value of configuration parameter with given *name* to *value*. """

    @property
    @abstractmethod
    def server_url(self) -> Optional[str]:
        """ Get the current value of the server URL. May be None, if not configured yet. """

    @server_url.setter
    @abstractmethod
    def server_url(self, server_url: str):
        """ Set the the server URL to *server_url*. """
