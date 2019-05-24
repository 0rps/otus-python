import os
import gzip
import sys
import glob
import logging
import collections
import time

from optparse import OptionParser
from threading import Thread
from queue import Queue

import memcache
import appsinstalled_pb2


NORMAL_ERR_RATE = 0.01
RECONNECT_TIMEOUT = 0.5
RECONNECT_ATTEMPT_COUNT = 5
MAX_THREADS = 5
AppsInstalled = collections.namedtuple("AppsInstalled", ["dev_type", "dev_id", "lat", "lon", "apps"])


class FileInfo:

    def __init__(self, filename):
        self.filename = filename
        self.processed = 0
        self.errors = 0
        self.__status = 'wait'

    def is_wait_status(self):
        return self.__status == 'wait'

    def is_run_status(self):
        return self.__status == 'run'

    def is_finished_status(self):
        return self.__status == 'finished'

    def set_run_status(self):
        self.__status = 'run'

    def set_finished_status(self):
        self.__status = 'finished'


class MemcachedConnectionError(Exception):
    pass


class MemcachedLoader:
    def __init__(self, address, dry_run=False):
        self.__address = address
        self.__dry_run = dry_run
        self.__memc = None
        self.__reconnect()

    def __reconnect(self):
        if self.__dry_run:
            return

        attempt = 0
        while attempt < RECONNECT_ATTEMPT_COUNT:
            if attempt > 0:
                time.sleep(RECONNECT_TIMEOUT)

            try:
                self.__client = memcache.Client([self.__address])
            except Exception as ex:
                print(ex)
                attempt += 1
            else:
                break

        if attempt == RECONNECT_ATTEMPT_COUNT:
            raise MemcachedConnectionError

    def load(self, appsinstalled, reconnect=True):
        ua = appsinstalled_pb2.UserApps()
        ua.lat = appsinstalled.lat
        ua.lon = appsinstalled.lon
        key = "%s:%s" % (appsinstalled.dev_type, appsinstalled.dev_id)
        ua.apps.extend(appsinstalled.apps)
        packed = ua.SerializeToString()
        try:
            if self.__dry_run:
                logging.debug("%s - %s -> %s" % (self.__address, key, str(ua).replace("\n", " ")))
            else:
                self.__client.set(key, packed)
            return True
        except Exception as e:
            if reconnect:
                try:
                    self.__reconnect()
                    return self.load(appsinstalled, False)
                except MemcachedConnectionError:
                    logging.exception("Cannot write to memc %s: %s" % (self.__address, e))
            return False


def dot_rename(path):
    head, fn = os.path.split(path)
    # atomic in most cases
    os.rename(path, os.path.join(head, "." + fn))


def parse_appsinstalled(line):
    line_parts = line.strip().split(b"\t")
    if len(line_parts) < 5:
        return

    dev_type, dev_id, lat, lon, raw_apps = line_parts
    if not dev_type or not dev_id:
        return

    try:
        apps = [int(a.strip()) for a in raw_apps.split(b",")]
    except ValueError:
        apps = [int(a.strip()) for a in raw_apps.split(b",") if a.isidigit()]
        logging.info("Not all user apps are digits: `%s`" % line)

    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        logging.info("Invalid geo coords: `%s`" % line)

    return AppsInstalled(dev_type, dev_id, lat, lon, apps)


def parse_appsinstalled_utf8(line):
    line_parts = line.strip().split("\t")
    if len(line_parts) < 5:
        return

    dev_type, dev_id, lat, lon, raw_apps = line_parts
    if not dev_type or not dev_id:
        return

    try:
        apps = [int(a.strip()) for a in raw_apps.split(",")]
    except ValueError as e:
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.strip().isdigit()]
        logging.info("Not all user apps are digits: `%s`" % line)

    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        logging.info("Invalid geo coords: `%s`" % line)

    return AppsInstalled(dev_type, dev_id, lat, lon, apps)


def reader_handler(filename: str, memc_loaders: dict, output_queue: Queue):
    errors = 0
    processed = 0

    logging.info("Starting file handling: {}".format(filename))
    fd = gzip.open(filename)
    handled = 0
    for line in fd:
        if handled % 500000 == 0 and handled > 0:
            logging.info("Handled {} lines of {}".format(handled, filename))

        line = line.decode('utf-8')
        line = line.strip()
        handled += 1
        if not line:
            continue

        appsinstalled = parse_appsinstalled_utf8(line)
        if not appsinstalled:
            errors += 1
            continue

        memc_loader = memc_loaders.get(appsinstalled.dev_type)
        if not memc_loader:
            errors += 1
            logging.error("Unknown device type: {}".format(appsinstalled.dev_type))
            continue

        try:
            memc_loader.load(appsinstalled)
        except MemcachedConnectionError:
            errors += 1
        else:
            processed += 1

    fd.close()
    output_queue.put((filename, processed, errors))


def find_files(pattern):
    result = collections.OrderedDict()
    for filename in glob.iglob(pattern):
        result[filename] = FileInfo(filename)

    return result


def start_file_readers(handler_func, available_threads, files, memc_loaders, message_queue):
    for key in files:
        if available_threads == 0:
            break

        fileinfo = files[key]
        if not fileinfo.is_wait_status():
            continue

        args = (fileinfo.filename, memc_loaders, message_queue)
        thread = Thread(target=handler_func, args=args)
        fileinfo.set_run_status()
        available_threads -= 1
        thread.start()

    return available_threads


def handle_processed_files(files):
    keys = list(files.keys())
    for key in keys:
        fileinfo = files[key]
        if not fileinfo.is_finished_status():
            break

        del files[key]

        err_rate = float(fileinfo.errors) / fileinfo.processed
        if err_rate < NORMAL_ERR_RATE:
            logging.info("Acceptable error rate (%s) for (%s). Successfull load" % (err_rate, fileinfo.filename))
        else:
            logging.error("High error rate (%s > %s). %s failed load" % (fileinfo.filename, err_rate, NORMAL_ERR_RATE))
        dot_rename(fileinfo.filename)


def main(memc_loaders_conf, pattern, dry_run):
    readers_queue = Queue()
    available_threads = MAX_THREADS
    memc_loaders = {key: MemcachedLoader(memc_loaders_conf[key], dry_run) for key in memc_loaders_conf.keys()}

    files = find_files(pattern)
    while len(files) > 0:
        available_threads = start_file_readers(reader_handler, available_threads, files, memc_loaders, readers_queue)

        message = readers_queue.get()
        processed_filename, processed, errors = message
        files[processed_filename].set_finished_status()
        files[processed_filename].errors = errors
        files[processed_filename].processed = processed

        handle_processed_files(files)


if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-t", "--test", action="store_true", default=False)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("--dry", action="store_true", default=False)
    op.add_option("--pattern", action="store", default="/data/appsinstalled/*.tsv.gz")
    op.add_option("--idfa", action="store", default="127.0.0.1:33013")
    op.add_option("--gaid", action="store", default="127.0.0.1:33014")
    op.add_option("--adid", action="store", default="127.0.0.1:33015")
    op.add_option("--dvid", action="store", default="127.0.0.1:33016")
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO if not opts.dry else logging.DEBUG,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    if opts.test:
        # TODO: run TestMemcLoad
        sys.exit(0)

    memc_servers = {
        'idfa': opts.idfa,
        'gaid': opts.gaid,
        'adid': opts.adid,
        'dvid': opts.dvid
    }

    logging.info("Memc loader started with options: %s" % opts)
    try:
        main(memc_servers, opts.pattern, opts.dry)
    except Exception as e:
        logging.exception("Unexpected error: %s" % e)
        sys.exit(1)
