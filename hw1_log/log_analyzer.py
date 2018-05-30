#!/usr/bin/env python3
import os
import re
import json
import gzip
import argparse
import logging
import shutil
from collections import defaultdict

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ERROR_THRESHOLD": 0.6,
    "LOG_FILE": None
}


def make_path(filepath, is_dir=False):
    """
    Make path for file or for dir
    :param filepath: target file or dir
    :param is_dir: is filepath is dir
    :return: None
    """
    dirname = filepath if is_dir else os.path.dirname(filepath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def write_report(data, report_dir, filename):
    """
    Generate report
    :param data: data for report
    :param report_dir: dir for report
    :param filename: name of report
    :return: success flag
    """
    logging.info("Report generation")

    marker = '$table_json'
    template_name = 'report.html'
    jquery_file = 'jquery.tablesorter.min.js'
    data_dir = 'data'

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 data_dir,
                                 template_name)
    if not os.path.exists(template_path):
        logging.error('No template file for report')
        raise Exception()

    make_path(report_dir, True)
    report_path = os.path.join(report_dir, filename)
    with open(report_path, 'w') as target:
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

    jquery_file_path_src = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        data_dir,
        jquery_file)
    jquery_file_path_dst = os.path.join(report_dir, jquery_file)
    shutil.copyfile(jquery_file_path_src, jquery_file_path_dst)

    logging.info("Success: {} generated".format(filename))
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
        raise Exception()

    msg = "File parsed: lines = {}, success lines = {}, error lines = {}"
    msg = msg.format(total_count,
                     total_count - not_parsed_count,
                     not_parsed_count)
    logging.info(msg)

    data = list(data.values())

    data.sort(key=lambda x: x['time_sum'], reverse=True)
    data = data[:min(report_size, len(data))]

    for time_data in data:
        time_data['times'].sort()
        sorted_times = time_data['times']

        count = len(sorted_times)
        center_idx = count // 2
        if count % 2 == 0:
            time_med = sorted_times[center_idx]
            time_med += sorted_times[center_idx - 1]
            time_med = time_med / 2.0
        else:
            time_med = sorted_times[center_idx]

        time_max = sorted_times[-1]
        time_avg = time_data['time_sum'] / count

        time_data['count'] = count
        time_data['count_perc'] = round(count * 100 / total_count, 3)
        time_perc = time_data['time_sum'] * 100 / total_time
        time_data['time_perc'] = round(time_perc, 3)
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
    regex = re.compile(r'(?P<name>nginx-access-ui\.log-'
                       r'(?P<date>\d{8}))(?P<ext>(?:\.gz)?)$')
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

            if res_date is None or (cur_date and cur_date > res_date):
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
        match = regex.match(file)
        is_gzip = match.group('ext') == '.gz'
        date = match.group('date')
        filepath = os.path.join(log_dir, file)
        logging.info("Success: last nginx log file {}"
                     .format(os.path.basename(filepath)))

    return filepath, date, is_gzip


def main(cfg):
    """
    Find last log file, process it and write report
    :param cfg: configuration
    :return: success flag
    """
    conf_report_size = cfg['REPORT_SIZE']
    conf_report_dir = cfg['REPORT_DIR']
    conf_log_dir = cfg['LOG_DIR']
    conf_threshold = cfg['ERROR_THRESHOLD']

    log_filepath, log_date, log_is_gzip = find_last_log(conf_log_dir)
    if log_filepath is None:
        logging.info("No log file for processing")
        return

    report_name = "report-{}.{}.{}.html".format(log_date[:4],
                                                log_date[4:6],
                                                log_date[6:])
    if os.path.exists(os.path.join(conf_report_dir, report_name)):
        logging.info("Report exists")
        return

    log_stream = read_log_file(log_filepath, log_is_gzip)
    data = process_log(log_stream, conf_report_size, conf_threshold)

    write_report(data, conf_report_dir, report_name)


def read_config(filepath):
    """
    Read configuration from file
    :param filepath: Config file path
    :return: config
    """
    conf = config.copy()
    with open(filepath) as fp:
        file_data = json.load(fp)
        conf.update(file_data)

    return conf


def configure_logging(log_file=None):
    """
    Configure logging
    :param log_file: output log file
    """
    if log_file is not None:
        make_path(log_file)

    msgfmt = '[%(asctime)s] %(levelname).1s %(message)s'
    datefmt = '%Y.%m.%d %H:%M:%S'
    logging.basicConfig(format=msgfmt, datefmt=datefmt,
                        filename=log_file, level=logging.INFO)

    logging.info("Success: logging configured")


if __name__ == "__main__":
    argp = argparse.ArgumentParser(description="Log analyzer")
    argp.add_argument('--config',
                      default='config.json',
                      help='Set config file')

    args = argp.parse_args()
    configuration = read_config(args.config)
    configure_logging(configuration['LOG_FILE'])

    try:
        main(configuration)
    except SystemExit as ex:
        if ex.code != 0:
            logging.exception("Exit with error")
            exit(ex.code)
    except:
        logging.exception("Caught exception")
