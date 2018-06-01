#!/usr/bin/env python3
import os
import re
import json
import gzip
import argparse
import logging
import shutil
import uuid
from datetime import datetime
from string import Template
from collections import defaultdict, namedtuple

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ERROR_THRESHOLD": 0.6,
    "LOG_FILE": None
}

RequestInfo = namedtuple('RequestInfo', ['url', 'time'])
ParsedData = namedtuple('ParsedData', ['data', 'total_time', 'total_count'])
LogFileShortInfo = namedtuple('LogFileShortInfo', ['name', 'date', 'is_gzip'])

log_line_regex = re.compile(r'[^\"]+'
                            r'\"'
                            r'\w+\s(?P<url>[^\s]+)\s[^\"]+'
                            r'\"'
                            r'(?:.|\s)+\s'
                            r'(?P<time>\d+\.\d+)')

log_filename_regex = re.compile(r'nginx-access-ui\.log-'
                                r'(?P<date>\d{8})(?P<ext>(?:\.gz)?)$')


def make_path(filepath):
    """
    Make dir path for file
    :param filepath: target file or dir
    :return: None
    """
    filepath = os.path.abspath(filepath)
    dirname = os.path.dirname(filepath)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def write_report(data, report_path):
    """
    Generate report
    :param data: data for report
    :param report_path: report file path
    :return: success flag
    """
    logging.info("Report generation")

    template_name = 'report.html'
    data_dir = 'data'

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 data_dir,
                                 template_name)
    if not os.path.exists(template_path):
        raise Exception('No template file for report')

    make_path(report_path)

    with open(template_path) as template_file:
        read_template = template_file.read()
        template = Template(read_template)

    json_data = json.dumps(data)
    report = template.safe_substitute(table_json=json_data)

    tmp_report = report_path + '.' + uuid.uuid4().hex + '.tmp'
    with open(tmp_report, 'w') as target:
        target.write(report)

    shutil.move(tmp_report, report_path)
    logging.info("Success: report generated: {}".format(report_path))


def parse_log_line(log_line):
    match = log_line_regex.match(log_line)
    if match:
        url, time = match.group('url'), float(match.group('time'))
        return RequestInfo(url, time)


def read_log_file(log_path, is_gzip):
    """
    Real log file, yield line by line
    :param log_path: Log file path
    :param is_gzip: Is gzipped:
    :return:
    """
    open_func = gzip.open if is_gzip else open
    for log_line in open_func(log_path, mode='rt', encoding='utf-8'):
        yield parse_log_line(log_line)


def process_log_stream(stream, threshold):
    """
    Parse log stream
    :param stream: log stream
    :param threshold: error threshold
    :return: parsed log info
    """
    logging.info("Trying to parse nginx log stream")
    data = defaultdict(lambda: {'time_sum': 0.0, 'times': []})

    invalid_count = 0
    total_count = 0
    total_time = 0

    for request in stream:

        total_count += 1
        if request is None:
            invalid_count += 1
        else:
            url_data = data[request.url]
            url_data['url'] = request.url
            url_data['time_sum'] += request.time
            url_data['times'].append(request.time)
            total_time += request.time

    if invalid_count / total_count > threshold:
        raise Exception("Couldn't parse log stream, too much errors")

    valid_count = total_count - invalid_count
    msg = "Stream parsed: lines = {}, success lines = {}, error lines = {}"
    msg = msg.format(total_count,
                     valid_count,
                     invalid_count)

    logging.info(msg)

    return ParsedData(list(data.values()), total_time, valid_count)


def process_data(parsed_data, report_size):
    """
    Process url data
    :param parsed_data: parsed log data
    :param report_size: size of output data
    :return: processed data
    """

    logging.info("Processing url data")

    total_count = parsed_data.total_count
    total_time = parsed_data.total_time
    data = parsed_data.data

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

    logging.info("Success: url data successfully processed")
    return data


def parse_date(date_str):
    """
    Parse date from string YYYYMMdd
    :param date_str: date in str format
    :return: datetime
    """
    try:
        date = datetime.strptime(date_str, '%Y%m%d')
    except ValueError:
        return None

    return date


def find_last_log_from_list(log_dir_iter):
    """
    Find last log file
    :param regex: compiled filename regex
    :param log_dir_iter: listdir iterator
    :return: filename
    """
    res_match = None
    res_date = None

    for file in log_dir_iter:
        match = log_filename_regex.match(file)
        if match:
            cur_date = parse_date(match.group('date'))
            if cur_date is None:
                continue

            if res_date is None or cur_date > res_date:
                res_date = cur_date
                res_match = match

    if res_match is None:
        return None

    name = res_match.string
    is_gzip = res_match.group('ext') == '.gz'
    return LogFileShortInfo(name, res_date, is_gzip)


def find_last_log(log_dir):
    """
    Find last log, get listdir and put it in find_last_log_from_list
    :param log_dir: directory of log files
    :return: filepath, date of file, gzip flag
    """
    logging.info("Trying to find last nginx log file")

    file_info = find_last_log_from_list(os.listdir(log_dir))

    if file_info is None:
        logging.info("No nginx log file found")
        return

    logging.info("Success: last nginx log file {}".format(file_info.name))
    return file_info


def main(cfg):
    """
    Find last log file, process it and write report
    :param cfg: configuration
    :return: success flag
    """

    log_info = find_last_log(cfg['LOG_DIR'])
    if log_info is None:
        return

    report_name = log_info.date.strftime("report-%Y.%m.%d.html")
    report_path = os.path.join(cfg['REPORT_DIR'], report_name)
    if os.path.exists(report_path):
        logging.info("Report exists")
        return

    log_filepath = os.path.join(cfg['LOG_DIR'], log_info.name)
    log_stream = read_log_file(log_filepath, log_info.is_gzip)
    data = process_log_stream(log_stream, cfg['ERROR_THRESHOLD'])

    data = process_data(data, cfg['REPORT_SIZE'])
    write_report(data, report_path)


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
    except BaseException:
        logging.exception("Caught exception")
