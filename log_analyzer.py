#!/usr/bin/env python3
import os
import re
import json
import gzip
import argparse
import unittest
from logging import getLogger
from collections import defaultdict

logger = getLogger(__file__)

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "THRESHOLD": 0.6
}


def write_report(data, filepath):
    logger.info("Writing data to report")

    marker = '$table_json'
    template_name = 'report.html'

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), template_name)
    if not os.path.exists(template_path):
        logger.error('No template file for report')
        return False

    with open(filepath, 'w') as target:
        with open(template_path) as template:
            no_marker = True
            for line in template:
                if no_marker and marker in line:
                    line_start, line_end = line.split(marker)
                    target.write(line_start)
                    json.dump(data, target)
                    target.write(line_end)
                    no_marker = False
                else:
                    target.write(line)

    logger.info("Report {} is generated".format(os.path.basename(filepath)))
    return True


def log_line_regex():
    regex = re.compile(r'[^\"]+'
                       r'\"'
                       r'\w+\s(?P<url>[^\s]+)\s[^\"]+'
                       r'\"'
                       r'(?:.|\s)+\s'
                       r'(?P<time>\d+\.\d+)')

    return regex


def read_log_file(filepath, is_gzip):
    if is_gzip:
        with gzip.open(filepath) as file:
            for line in file:
                yield line.decode()
    else:
        with open(filepath) as file:
            for line in file:
                yield line


def handle_log(filepath, is_gzip, report_size, threshold):
    logger.info("Trying to handle file: {}".format(os.path.basename(filepath)))

    data = defaultdict(lambda: {'time_sum': 0.0, 'times': []})
    regex = log_line_regex()

    not_parsed_count = 0
    total_count = 0
    total_time = 0.0

    for log_line in read_log_file(filepath, is_gzip):
        match = regex.match(log_line)
        if match is None:
            not_parsed_count += 1
        else:
            url, time = match.group('url'), float(match.group('time'))
            url_data = data[match.group('url')]
            url_data['url'] = url
            url_data['times'].append(time)
            url_data['time_sum'] += time
            total_time += time

        total_count += 1

    if not_parsed_count / total_count > threshold:
        logger.error("Couldn't parse log file, too much errors")
        return

    logger.info("File parsed: lines = {}, success lines = {}, error lines = {}".format(total_count,
                                                                                       total_count - not_parsed_count,
                                                                                       not_parsed_count))

    data = list(data.values())

    data.sort(key=lambda x: x['time_sum'], reverse=True)
    data = data[:min(report_size, len(data))]

    for time_data in data:
        time_data['times'].sort()
        sorted_times = time_data['times']

        count = len(sorted_times)
        center_idx = count // 2
        if count % 2 == 0:
            time_med = (sorted_times[center_idx] + sorted_times[center_idx - 1]) / 2.0
        else:
            time_med = sorted_times[center_idx]

        time_max = sorted_times[-1]
        time_avg = time_data['time_sum'] / count

        time_data['count'] = count
        time_data['count_perc'] = round(count * 100 / total_count, 3)
        time_data['time_perc'] = round(time_data['time_sum'] * 100 / total_time, 3)
        time_data['time_max'] = round(time_max, 3)
        time_data['time_avg'] = round(time_avg, 3)
        time_data['time_med'] = round(time_med, 3)
        time_data['time_sum'] = round(time_data['time_sum'], 3)

        del time_data['times']

    logger.info("Log file successfully handled")

    return data


def log_filename_regex():
    regex = re.compile(r'(?P<name>nginx\-access\-ui\.log\-(?P<date>\d{8}))(?P<ext>(?:\.gz)?)$')
    return regex


def find_last_log(log_dir):
    logger.info("Trying to find last log file")
    filepath = None
    date = None
    is_gzip = None

    regex = log_filename_regex()

    for file in os.listdir(log_dir):
        match = regex.match(file)
        if match:
            cur_date = match.group('date')
            if (cur_date and date and cur_date > date) or date is None:
                date = cur_date
                filepath = os.path.join(log_dir, file)
                is_gzip = match.group('ext') == '.gz'

    if filepath is None:
        logger.info("No log file found")
    else:
        logger.info("Last log file: {}".format(os.path.basename(filepath)))

    return filepath, date, is_gzip


def release_mode(conf):
    conf_report_size = conf['REPORT_SIZE']
    conf_report_dir = conf['REPORT_DIR']
    conf_log_dir = conf['LOG_DIR']
    conf_threshold = conf['THRESHOLD']

    log_filepath, log_date, log_is_gsip = find_last_log(conf_log_dir)
    if log_filepath is None:
        return

    report_name = "report-{}.{}.{}.html".format(log_date[:4], log_date[4:6], log_date[6:])
    output_path = os.path.join(conf_report_dir, report_name)
    if os.path.exists(output_path):
        logger.info("Report for this file exists")
        pass

    data = handle_log(log_filepath, log_is_gsip, conf_report_size, conf_threshold)
    if data is None:
        return

    if not write_report(data, output_path):
        return


def read_config(filepath=None):
    logger.info('Handle program configuration')
    conf = config.copy()

    if filepath:
        logger.info('Trying to parse config file')
        if not os.path.exists(filepath):
            logger.error("Config file doesn't exist")
            return

        try:
            file_data = json.loads(filepath)
        except json.JSONDecodeError:
            logger.error("Couldn't parse config file")
            return
        else:
            conf.update(file_data)
    logger.info('Success: configuration handled')
    return conf


def main():
    argp = argparse.ArgumentParser(description="Nginx log report handler")
    argp.add_argument('--config', default='config.json', help='Set config file')
    argp.add_argument('--run-test', help='Run unit tests')

    args = vars(argp.parse_args())

    config_file = None
    if 'config' in args:
        config_file = args['config']

    if 'run-test' in args:
        unittest.main()
    else:
        conf = read_config(config_file)
        if conf is None:
            return
        release_mode(conf)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        logger.exception("Caught exception")
