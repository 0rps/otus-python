#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from logging import getLogger

logger = getLogger(__file__)

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def read_config():
    return config


def get_last_log(log_dir):
    logname = 'nginx-access-ui.log-20170630'
    return os.path.join(log_dir, logname), logname, False


def is_report_exists(report_name, report_dir):
    if report_name is None:
        return False

    return os.path.exists(os.path.join(report_dir, report_name))


def parse_log_line(log_line):
    re.compile(r'^[.\s]*'
               r'\"\w+\s(.+)\s.+\"'
               r'[.\s\"]*'
               r'(\d+\.\d+)$')
    print(log_line)
    return None


def read_log(filepath, is_gzip):
    data = {}
    read_count = 0
    parsed_count = 0
    with open(filepath) as fd:
        for line in fd:
            line_data = parse_log_line(line)
            if len(line) > 0 and line_data is not None:
                data[line_data['url']] = line_data
                parsed_count += 1

            read_count += 1

    return data


def write_to_template(log_data, filepath, report_size):
    pass


def main():
    cur_config = read_config()
    report_dir = cur_config['REPORT_DIR']
    report_size = cur_config['REPORT_SIZE']
    log_dir = cur_config['LOG_DIR']

    log_filepath, log_name, is_gzip = get_last_log(log_dir)

    report_filepath = os.path.join(log_name, report_dir)
    if os.path.exists(report_filepath):
        logger.info("Log '{}' exists".format(log_name))
        pass

    log_data = read_log(log_filepath, is_gzip)
    write_to_template(log_data, report_filepath, report_size)


if __name__ == "__main__":
    main()
