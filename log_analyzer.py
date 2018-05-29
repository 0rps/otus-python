#!/usr/bin/env python3
import os
import re
import json
import gzip
import argparse
import logging
from collections import defaultdict

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ERROR_THRESHOLD": 0.6,
    "LOG_FILE": None
}


def write_report(data, filepath):
    """
    Generate report
    :param data: data for report
    :param filepath: path of report
    :return: success flag
    """
    logging.info("Report generation")

    marker = '$table_json'
    template_name = 'report.html'

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), template_name)
    if not os.path.exists(template_path):
        logging.error('No template file for report')
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

    logging.info("Success: {} generated".format(os.path.basename(filepath)))
    return True


def log_line_regex():
    """
    Regex for log line parsing
    :return: regex
    """
    regex = re.compile(r'[^\"]+'
                       r'\"'
                       r'\w+\s(?P<url>[^\s]+)\s[^\"]+'
                       r'\"'
                       r'(?:.|\s)+\s'
                       r'(?P<time>\d+\.\d+)')

    return regex


def read_log_file(filepath, is_gzip):
    """
    Read log file (plain text or gzipped data)
    :param filepath: path of log
    :param is_gzip: is gzip file
    :return: generator
    """
    if is_gzip:
        with gzip.open(filepath) as file:
            for line in file:
                yield line.decode()
    else:
        with open(filepath) as file:
            for line in file:
                yield line


def process_log(stream, report_size, threshold):
    """
    Parse log file, process url data
    :param stream: log stream
    :param report_size: size of output data
    :param threshold: error threshold
    :return: processed data
    """
    logging.info("Trying to process nginx log file")

    data = defaultdict(lambda: {'time_sum': 0.0, 'times': []})
    regex = log_line_regex()

    not_parsed_count = 0
    total_count = 0
    total_time = 0.0

    for log_line in stream:
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
        logging.error("Couldn't parse log file, too much errors")
        return

    logging.info("File parsed: lines = {}, success lines = {}, error lines = {}".format(total_count,
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

    logging.info("Success: log file successfully processed")

    return data


def log_filename_regex():
    """
    Regex for log filename
    :return: regex
    """
    regex = re.compile(r'(?P<name>nginx-access-ui\.log-(?P<date>\d{8}))(?P<ext>(?:\.gz)?)$')
    return regex


def check_strdate(date_str):
    """
    Check if date is valid
    :param date_str: date in str format
    :return: is valid
    """
    year = int(date_str[:4])
    month = int(date_str[4:6])
    day = int(date_str[6:])

    if year < 1970:
        return False

    if month == 0 or month > 12:
        return False

    if day == 0 or day > 31:
        return False

    return True


def find_last_log_from_list(regex, log_dir_iter):
    """
    Find last log file
    :param regex: compiled filename regex
    :param log_dir_iter: listdir iterator
    :return: filename
    """
    res_file = None
    res_date = None

    for file in log_dir_iter:
        match = regex.match(file)
        if match:
            cur_date = match.group('date')
            if cur_date is None or not check_strdate(cur_date):
                continue

            if res_date is None or (cur_date and res_date and cur_date > res_date):
                res_date = cur_date
                res_file = file

    return res_file


def find_last_log(log_dir):
    """
    Find last log, get listdir and put it in find_last_log_from_list
    :param log_dir: directory of log files
    :return: filepath, date of file, gzip flag
    """
    logging.info("Trying to find last nginx log file")
    date = None
    filepath = None
    is_gzip = None

    regex = log_filename_regex()
    file = find_last_log_from_list(regex, os.listdir(log_dir))

    if file is None:
        logging.info("No nginx log file found")
    else:
        is_gzip = regex.match(file).group('ext') == '.gz'
        filepath = os.path.join(log_dir, file)
        logging.info("Success: last nginx log file {}".format(os.path.basename(filepath)))

    return filepath, date, is_gzip


def run_analyzer(conf):
    """
    Find last log file, process it and write report
    :param conf: configuration
    :return: success flag
    """
    conf_report_size = conf['REPORT_SIZE']
    conf_report_dir = conf['REPORT_DIR']
    conf_log_dir = conf['LOG_DIR']
    conf_threshold = conf['ERROR_THRESHOLD']

    log_filepath, log_date, log_is_gzip = find_last_log(conf_log_dir)
    if log_filepath is None:
        return True

    report_name = "report-{}.{}.{}.html".format(log_date[:4], log_date[4:6], log_date[6:])
    output_path = os.path.join(conf_report_dir, report_name)
    if os.path.exists(output_path):
        logging.info("Report exists")
        return True

    log_stream = read_log_file(log_filepath, log_is_gzip)
    data = process_log(log_stream, conf_report_size, conf_threshold)
    if data is None:
        return False

    if not write_report(data, output_path):
        return False


def read_config(filepath=None):
    """
    Read configuration from file, setup logging
    :param filepath: Config file
    :return: config
    """
    conf = config.copy()

    if filepath:
        if not os.path.exists(filepath):
            exit(-1)

        try:
            file_data = json.loads(filepath)
        except json.JSONDecodeError:
            exit(-1)
        else:
            conf.update(file_data)

    if 'LOG_FILE' in conf and conf['LOG_FILE'] is not None:
        log_file = conf['LOG_FILE']
        msgfmt = '[%(asctime)s] %(levelname).1s %(message)s'
        datefmt = '%Y.%m.%d %H:%M:%S'
        logging.basicConfig(format=msgfmt, datefmt=datefmt, filename=log_file, level=logging.INFO)
        del conf['LOG_FILE']

    logging.info('Success: configured')

    return conf


def main():
    """
    Read cmd arguments, setup config, run analyzer
    """
    argp = argparse.ArgumentParser(description="Nginx log report handler")
    argp.add_argument('--config', nargs='?', const='config.json', help='Set config file')

    args = vars(argp.parse_args())

    config_file = None
    if 'config' in args:
        config_file = args['config']

    conf = read_config(config_file)

    if not run_analyzer(conf):
        exit(-1)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        logging.exception("Caught exception")
