import unittest
from unittest import mock
import time
import gzip
import os
import queue
import tempfile
import appsinstalled_pb2
import memc_load
import collections
import memcache
import subprocess


class TestUtils(unittest.TestCase):

    def test_dot_rename(self):
        fd, filename = tempfile.mkstemp()
        os.close(fd)

        h, t = os.path.dirname(filename), os.path.basename(filename)
        new_filename = os.path.join(h, '.' + t)

        self.assertFalse(os.path.exists(new_filename))
        memc_load.dot_rename(filename)
        self.assertTrue(os.path.exists(new_filename))

    def test_proto(self):
        sample = "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567,3,7,23\ngaid\t7rfw452y52g2gq4g\t55.55\t42.42\t7423,424"
        for line in sample.splitlines():
            dev_type, dev_id, lat, lon, raw_apps = line.strip().split("\t")
            apps = [int(a) for a in raw_apps.split(",") if a.isdigit()]
            lat, lon = float(lat), float(lon)
            ua = appsinstalled_pb2.UserApps()
            ua.lat = lat
            ua.lon = lon
            ua.apps.extend(apps)
            packed = ua.SerializeToString()
            unpacked = appsinstalled_pb2.UserApps()
            unpacked.ParseFromString(packed)
            assert ua == unpacked


class TestMemcLoad(unittest.TestCase):

    def setUp(self):
        patch = mock.patch('memc_load.dot_rename')
        self.mock_1 = patch.start()
        self.addCleanup(patch.stop)

    def test_start_file_readers__little_avail_threads(self):
        called_count = 0

        def stub_func(*args, **kwargs):
            nonlocal called_count
            called_count += 1

        avail_threads = 2
        files = {x: memc_load.FileInfo('') for x in range(avail_threads+2)}
        memc_load.start_file_readers(stub_func, avail_threads, files, {}, queue.Queue())
        time.sleep(0.5)

        self.assertEqual(avail_threads, called_count)

    def test_start_file_readers__little_files(self):
        called_count = 0

        def stub_func(*args, **kwargs):
            nonlocal called_count
            called_count += 1

        avail_threads = 5
        self.assertTrue(avail_threads > 3)

        files = {x: memc_load.FileInfo('') for x in range(avail_threads - 2)}
        memc_load.start_file_readers(stub_func, avail_threads, files, {}, queue.Queue())
        time.sleep(0.5)

        self.assertEqual(len(files), called_count)

    def test_start_files_readers__files_with_wait_status(self):
        called_count = 0

        def stub_func(*args, **kwargs):
            nonlocal called_count
            called_count += 1

        avail_threads = 5
        self.assertTrue(avail_threads > 3)

        files = {x: memc_load.FileInfo('') for x in range(avail_threads - 2)}
        files[0].set_run_status()
        files[1].set_run_status()
        memc_load.start_file_readers(stub_func, avail_threads, files, {}, queue.Queue())
        time.sleep(0.5)

        self.assertEqual(len(files)-2, called_count)

    def test_parse_appsinstalled__wrong_parts_count(self):
        line = "1\t2\t3\t4"
        self.assertIsNone(memc_load.parse_appsinstalled_utf8(line))

    def test_parse_appsinstalled__wrong_dev(self):
        line = "1\t\t\t4\t5"
        self.assertIsNone(memc_load.parse_appsinstalled_utf8(line))

    def test_parse_appsinstalled__wrong_apps(self):
        line = "1\t2\t3\t4\txabc, 1234 ,xggf"
        appsinst = memc_load.parse_appsinstalled_utf8(line)
        self.assertListEqual(appsinst.apps, [1234])

    def test_parse_appsinstalled__wrong_coords(self):
        line = "1\t2\tlat\tlon\txabc, 1234 ,xggf"
        appsinst = memc_load.parse_appsinstalled_utf8(line)
        self.assertTrue(appsinst.lon == 'lon')
        self.assertTrue(appsinst.lat == 'lat')

    def test_parse_appsinstalled__success(self):
        line = "d_type\td_id\t3.667\t359.12\t44,xabc, 1234 ,xggf"
        appsinst = memc_load.parse_appsinstalled_utf8(line)
        self.assertAlmostEqual(appsinst.lat, 3.667)
        self.assertAlmostEqual(appsinst.lon, 359.12)
        self.assertTrue(appsinst.dev_id, 'd_id')
        self.assertTrue(appsinst.dev_type, 'd_type')
        self.assertListEqual(appsinst.apps, [44, 1234])

    def test_handle_processed_files__remove_from_start(self):
        files = collections.OrderedDict()
        files['1'] = memc_load.FileInfo('1')
        files['2'] = memc_load.FileInfo('2')
        files['3'] = memc_load.FileInfo('3')

        files['1'].set_finished_status()
        files['1'].processed = 1
        files['2'].set_finished_status()
        files['2'].processed = 1
        files['3'].set_run_status()

        memc_load.handle_processed_files(files)
        self.assertEqual(len(files), 1)

    def test_handle_processed_files__not_finished_at_start(self):
        files = collections.OrderedDict()
        files['1'] = memc_load.FileInfo('1')
        files['2'] = memc_load.FileInfo('2')
        files['3'] = memc_load.FileInfo('3')

        files['1'].set_run_status()
        files['1'].processed = 1
        files['2'].set_finished_status()
        files['2'].processed = 1
        files['3'].set_run_status()

        memc_load.handle_processed_files(files)
        self.assertEqual(len(files), 3)

    @mock.patch("memcache.Client")
    def test_reader_handler__success(self, client_class):
        _, filename = tempfile.mkstemp()

        fd = gzip.open(filename, 'wb')
        fd.write(b'dev_b\tdev_b\t1\t1\t1\t')
        fd.close()

        reader_queue = queue.Queue()
        memc_load.reader_handler(filename, {'dev_a': memc_load.MemcachedLoader('127.0.0.1:8000')}, reader_queue)
        os.remove(filename)

        message = reader_queue.get_nowait()
        self.assertEqual(len(message), 3)
        self.assertEqual(message[0], filename)
        self.assertEqual(message[1], 0)
        self.assertEqual(message[2], 1)

    @mock.patch("memcache.Client")
    def test_reader_handler__parse_error(self, memc_class):
        _, filename = tempfile.mkstemp()

        fd = gzip.open(filename, 'wb')
        fd.write(b'\tdev_b\t1\t1\t1')
        fd.close()

        reader_queue = queue.Queue()
        memc_load.reader_handler(filename, {'dev_a': memc_load.MemcachedLoader('127.0.0.1:8000')}, reader_queue)
        os.remove(filename)

        message = reader_queue.get_nowait()
        self.assertEqual(len(message), 3)
        self.assertEqual(message[0], filename)
        self.assertEqual(message[1], 0)
        self.assertEqual(message[2], 1)

    def test_reader_handler__memcached_error(self):
        memc_mock = mock.Mock()
        memc_mock.load.side_effect = memc_load.MemcachedConnectionError()

        _, filename = tempfile.mkstemp()

        fd = gzip.open(filename, 'wb')
        fd.write(b'dev_a\tdev_a\t1\t1\t1\t')
        fd.close()

        reader_queue = queue.Queue()
        memc_load.reader_handler(filename, {'dev_a': memc_mock}, reader_queue)
        os.remove(filename)

        message = reader_queue.get_nowait()
        self.assertEqual(len(message), 3)
        self.assertEqual(message[0], filename)
        self.assertEqual(message[1], 0)
        self.assertEqual(message[2], 1)

    @mock.patch("memcache.Client")
    def test_reader_handler__unknown_device(self, memc_class):
        _, filename = tempfile.mkstemp()

        fd = gzip.open(filename, 'wb')
        fd.write(b'dev_a\tdev_a\t1\t1\t1\t')
        fd.close()

        reader_queue = queue.Queue()
        memc_load.reader_handler(filename, {'dev_b': memc_load.MemcachedLoader('127.0.0.1:8000')}, reader_queue)
        os.remove(filename)

        message = reader_queue.get_nowait()
        self.assertEqual(len(message), 3)
        self.assertEqual(message[0], filename)
        self.assertEqual(message[1], 0, "Wrong number of processed")
        self.assertEqual(message[2], 1, "Wrong number of errors")
        print(message)


class TestMemcachedLoader(unittest.TestCase):

    def setUp(self):
        self.memc_service = subprocess.Popen(["memcached", "-p", "44551"], shell=True)
        time.sleep(1)

    def tearDown(self):
        self.memc_service.terminate()

    @mock.patch("memcache.Client")
    def test_dry_run(self, memc_class):
        memc_class.side_effect = Exception()
        loader = memc_load.MemcachedLoader('address', True)
        apps = memc_load.AppsInstalled('1234', '1234', 1, 2, [1234])
        loader.load(apps)
        self.assertTrue(memc_class.call_count == 0)

    @mock.patch("memcache.Client")
    def test_unsuccess_connect(self, memc_class):
        memc_class.side_effect = Exception
        with self.assertRaises(memc_load.MemcachedConnectionError):
            memc_load.MemcachedLoader('address')

    def test_success_connect(self):
        loader = memc_load.MemcachedLoader('127.0.0.1:44551')

    def test_success_load(self):
        loader = memc_load.MemcachedLoader('127.0.0.1:44551')
        apps = memc_load.AppsInstalled('1234', '1234', 1, 2, [1234])
        loader.load(apps)

    @mock.patch("memcache.Client")
    def test_reconnect(self, memc_class):
        memc_class.side_effect = [Exception(), Exception(), mock.Mock()]
        memc_load.MemcachedLoader('address')
        self.assertTrue(memc_class.call_count, 3)


if __name__ == '__main__':
    unittest.main()
