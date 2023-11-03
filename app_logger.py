import datetime
import inspect
import json
import logging


class JSONFormatter(logging.Formatter):
    def format(self, record):
        message = json.loads(
            record.getMessage().encode("utf-8")
        )

        log_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f"),
            "level": record.levelname,
            "message": message
        }

        return json.dumps(log_data, ensure_ascii=False, indent=4)


class Logger:
    def __init__(self, filename):
        self.logger = logging.getLogger(filename)
        self.logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(JSONFormatter())

        self.logger.addHandler(file_handler)

    def log(self, message):
        self.logger.info(message)


class AppLogger:
    def __init__(self, request_response_logger_filename):
        self.request_response_logger = Logger(request_response_logger_filename)

    def log_request_response(self, response):
        stack = inspect.stack()
        caller_frame = stack[2]
        caller_class = caller_frame.frame.f_locals['self'].__class__.__name__
        caller_method = caller_frame.function

        log_data = {
            "caller": "{}.{}".format(caller_class, caller_method),
            "request": {
                "url": response.request.url,
                "method": response.request.method,
                "headers": dict(response.request.headers),
                "data": json.loads(response.request.body.decode("utf-8")) if response.request.body else None
            },
            "response": {
                "status code": response.status_code,
                "headers": dict(response.headers),
                "data": response.json(),
            }
        }

        log_data_json = json.dumps(log_data)

        self.request_response_logger.log(log_data_json)


# Configure the root logger with a JSONFormatter
# root_logger = logging.getLogger()
# root_logger.setLevel(logging.INFO)
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(JSONFormatter())
# root_logger.addHandler(console_handler)
