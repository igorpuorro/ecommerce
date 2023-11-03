import json
import os
import re
import sys

import requests

from datetime import datetime
from urllib.parse import urlparse
from prettytable import PrettyTable, FRAME, HEADER, NONE


class LogTools:
    app_root_path: str = ".."
    download_directory: str
    log_records: list

    def __init__(self, file_path: str):
        self.log_records = self._load_json_records(file_path)

        self.app_root_path = os.path.abspath(self.app_root_path)
        self.download_directory = os.path.join(self.app_root_path, "downloads")

        if not os.path.exists(self.download_directory):
            os.makedirs(self.download_directory)

    def _load_json_records(self, file_path) -> list:
        records = []
        record = ""

        with open(file_path, 'r') as file:
            for line in file:
                record += line
                try:
                    json_record = json.loads(record)
                    records.append(json_record)
                    record = ""

                except json.JSONDecodeError:
                    pass

        return records

    def query_records(self, condition_url: str):
        parsed_condition_url = urlparse(condition_url)
        condition_url_host = f"{parsed_condition_url.scheme}{parsed_condition_url.netloc}"
        condition_url_path = parsed_condition_url.path

        records_to_delete = []
        for index, record in enumerate(self.log_records):
            try:
                url = record.get(
                    "message", {}).get(
                    "request", {}).get(
                    "url", "")

                parsed_url = urlparse(url)
                parsed_host = f"{parsed_url.scheme}{parsed_url.netloc}"
                parsed_path = parsed_url.path

                if condition_url_host not in parsed_host or condition_url_path not in parsed_path:
                    records_to_delete.append(index)

            except Exception:
                continue

        # Delete records based on their indices in reverse order to avoid index shifting
        for index in reversed(records_to_delete):
            del self.log_records[index]

        return self.log_records

    def filter_file_list(self) -> list:
        file_list = []

        for record in self.log_records:
            try:
                url = record.get(
                    "message", {}).get(
                    "request", {}).get(
                    "url", "")

                data_file_list = record.get(
                    "message", {}).get(
                    "response", {}).get(
                    "data", {}).get(
                    "file_list", "")

                if url.strip() and data_file_list:
                    file_list.append({url: data_file_list})

            except Exception:
                continue

        return file_list

    def file_list(self, file_list: str) -> list:
        result_dict = {}

        for entry in file_list:
            url = list(entry.keys())[0]
            data = entry[url]

            if url in result_dict:
                for item in data:
                    filename = item["filename"]
                    timestamp = float(item["timestamp"])
                    existing_data = result_dict[url]

                    for existing_item in existing_data:
                        if existing_item["filename"] == filename:
                            if timestamp > float(existing_item["timestamp"]):
                                existing_item["timestamp"] = str(timestamp)
                            break
                    else:
                        existing_data.append(
                            {"filename": filename, "timestamp": str(timestamp)}
                        )

                # Sort by filename
                existing_data.sort(key=lambda x: x["filename"])
            else:
                result_dict[url] = data

        return [
            {url: sorted(result_dict[url], key=lambda x: x["filename"])} for url in result_dict
        ]

    def print_file_list(self, source_file_list: list, filename_substring: str = ""):
        for url_file_list_dict in source_file_list:
            for url, file_list in url_file_list_dict.items():
                table = PrettyTable()
                table.align = "l"
                table.header = True
                table.field_names = ["Filename", "Timestamp"]

                for item in file_list:
                    if filename_substring.lower() not in item.get("filename", "").lower():
                        continue

                    timestamp_datetime = datetime.fromtimestamp(
                        float(item.get("timestamp"))
                    )
                    timestamp = timestamp_datetime.strftime(
                        '%Y-%m-%d %H:%M:%S'
                    )

                    table.add_row([
                        item.get('filename'),
                        timestamp
                    ])

                print(f"URL: {url}\n")
                print(table)
                print("")

    def download_file_list(self, source_file_list: list, filename_substring: str = "", overwrite: bool = False):
        if not os.path.exists(self.download_directory):
            raise FileNotFoundError()

        for url_file_list_dict in source_file_list:
            for url, file_list in url_file_list_dict.items():
                table = PrettyTable()
                table.align = "l"
                table.header = True
                table.field_names = [
                    "Filename", "Timestamp", "Local", "Download"
                ]

                for item in file_list:
                    if filename_substring.lower() not in item.get("filename", "").lower():
                        continue

                    file_path = os.path.join(
                        self.download_directory,
                        item.get("filename")
                    )

                    timestamp_datetime = datetime.fromtimestamp(
                        float(item.get("timestamp"))
                    )
                    timestamp = timestamp_datetime.strftime(
                        '%Y-%m-%d %H:%M:%S'
                    )

                    local = False

                    if os.path.isfile(file_path):
                        local = True

                    reponse_status_code = ""

                    if not os.path.isfile(file_path) or overwrite:
                        reponse_status_code = self._wsa_download_download(
                            url, item.get("filename")
                        )

                    table.add_row([
                        item.get('filename'),
                        timestamp,
                        local,
                        reponse_status_code
                    ])

                print(f"URL: {url}")
                print(f"Overwrite: {overwrite}\n")
                print(table)
                print("")

    def _wsa_download_download(self, url: str, filename: str):
        try:
            parsed_url = urlparse(url)
            parsed_url_host = f"{parsed_url.scheme}://{parsed_url.netloc}"

            endpoint = f"{parsed_url_host}/download/{filename}"

            response = requests.get(endpoint, timeout=300)
            response.raise_for_status()

            # Check if the response has the 'Content-Disposition' header to get the suggested file name.
            suggested_filename = response.headers.get("Content-Disposition")

            if suggested_filename:
                # Extract the filename from the header.
                suggested_filename = re.findall(
                    "filename=(.+)", suggested_filename
                )

                if suggested_filename:
                    suggested_filename = suggested_filename[0].strip('"')

            local_path = os.path.join(
                self.download_directory,
                suggested_filename
            )

            with open(local_path, "wb") as f:
                f.write(response.content)

            return response.status_code

        except requests.exceptions.RequestException as error:
            return error.response.status_code


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    # condition_url = "http://api.craftbrewer.com.br:5000/correios/enderecador/encomendas"
    condition_url = "/correios/enderecador/encomendas"

    log_tools = LogTools(file_path)
    log_tools.query_records(condition_url=condition_url)

    filtered_file_list = log_tools.filter_file_list()
    file_list = log_tools.file_list(filtered_file_list)

    # log_tools.print_file_list(file_list)

    log_tools.download_file_list(file_list, overwrite=False)


if __name__ == "__main__":
    main()
