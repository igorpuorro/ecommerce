import json
import configparser


class JSONConfigParser(configparser.ConfigParser):
    def read_json(self, filename):
        try:
            with open(filename, "r") as json_file:
                data = json.load(json_file)
                for section, settings in data.items():
                    self[section] = settings

        except FileNotFoundError:
            raise FileNotFoundError(f"Config file '{filename}' not found.")
        except json.JSONDecodeError:
            raise ValueError(f"Error parsing JSON in '{filename}'.")
