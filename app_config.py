import json
import configparser

from json_config_parser import JSONConfigParser


class AppConfig:
    def __init__(self, config_file_path: str):
        self.config = JSONConfigParser()
        self.config.read_json(config_file_path)

    def get(self, section: str, option: str):
        try:
            return self.config.get(section, option)

        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def has_option(self, section: str, option: str):
        return self.config.has_option(section, option)
