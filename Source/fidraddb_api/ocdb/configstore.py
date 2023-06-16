import json
import os
import stat
from abc import ABCMeta, abstractmethod
from typing import Any, Dict

#from const import CONFIG_FILE_MODE, CONFIG_DIR_MODE

Config = Dict[str, Any]

CONFIG_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR
CONFIG_DIR_MODE = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR


class ConfigStore(metaclass=ABCMeta):
    @abstractmethod
    def read(self) -> Config:
        """
        Read a configuration.
        Returns a JSON-serializable configuration Python dictionary.
        """

    @abstractmethod
    def write(self, config: Config):
        """
        Write a configuration *conf*which is a JSON-serializable configuration Python dictionary.
        """


class MemConfigStore(ConfigStore):
    def __init__(self, **config):
        self._config = config

    def read(self) -> Config:
        return dict(self._config)

    def write(self, config: Config):
        self._config.update(config)


class EnvConfigStore(ConfigStore):
    def __init__(self, **config):
        self._config = config

    def read(self) -> Config:
        for item in self._config:
            self._config[item] = os.environ[item.upper()] or self._config[item]
        return dict(self._config)

    def write(self, config: Config):
        self._config.update(config)


class JsonConfigStore(ConfigStore):
    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            self.write({})

    def read(self) -> Config:
        if os.path.isfile(self.file_path):
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return {}

    def write(self, config: Config):
        dir_path = os.path.dirname(self.file_path)
        if dir_path and not os.path.isdir(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        with open(self.file_path, 'w') as fp:
            json.dump(config, fp, indent=4)

        if dir_path:
            os.chmod(dir_path, CONFIG_DIR_MODE)
        os.chmod(self.file_path, CONFIG_FILE_MODE)
