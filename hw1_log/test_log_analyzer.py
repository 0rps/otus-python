import unittest
import itertools as it
from datetime import datetime
import log_analyzer as logan


class TestLogAnalyzer(unittest.TestCase):

    def test_regex_filename(self):
        """
        Check filename regex correctness
        """

        regex = logan.log_filename_regex
        match = regex.match("nginx-access-ui.log-11112233.gz1")
        self.assertEqual(match, None)
        match = regex.match("nginx-access-ui.log-111122334")
        self.assertEqual(match, None)
        match = regex.match("nginx_-access-ui.log-11112233")
        self.assertEqual(match, None)

        match = regex.match("nginx-access-ui.log-20180220.gz")
        self.assertNotEqual(match, None)
        self.assertEqual(match.group('date'), '20180220')
        self.assertEqual(match.group('ext'), '.gz')

        match = regex.match("nginx-access-ui.log-20180221")
        self.assertNotEqual(match, None)
        self.assertEqual(match.group('date'), '20180221')
        self.assertEqual(match.group('ext'), '')

    def test_find_last_log(self):
        """
        Test search log
        """

        result_file = 'nginx-access-ui.log-20180227.gz'
        log_list = ['nginx-access-ui.log-20201521',
                    'nginx-access-ui.log-20180224.gz',
                    result_file,
                    'nginx-access-ui.log-20180225']

        last_log = logan.find_last_log_from_list(log_list)
        self.assertEqual(last_log.name, result_file)
        self.assertEqual(last_log.date, datetime(year=2018, month=2, day=27))
        self.assertTrue(last_log.is_gzip)

        result_file = 'nginx-access-ui.log-20190227'
        log_list = ['nginx-access-ui.log-20180224.gz',
                    result_file,
                    'nginx-access-ui.log-20180225']

        last_log = logan.find_last_log_from_list(log_list)
        self.assertEqual(last_log.name, result_file)

    def test_parse_log_line(self):
        """
        Check log line parsing
        """

        a1 = '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] ' \
             '"GET /api/v2/banner/7763463 HTTP/1.1" 200 1018 "-"' \
             ' "Configovod" "-" "1498697422-2118016444-4708-9752774"' \
             ' "712e90144abee9" 0.181'

        a2 = '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] ' \
             '"GET /api/v2/banner/7763463 HTTP/1.1" 200 1018 "-"' \
             ' "Configovod" "-" "1498697422-2118016444-4708-9752774" ' \
             '"712e90144abee9" 0181'

        a3 = '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] ' \
             '"GET /api/v2/banner/7763463 HTTP/1.1" 200 1018 "-"' \
             ' "Configovod" "-" "1498697422-2118016444-4708-9752774" ' \
             '"712e90144abee9"0.181'

        request = logan.parse_log_line(a1)
        self.assertNotEqual(request, None)
        self.assertEqual(request.url, '/api/v2/banner/7763463')
        self.assertAlmostEqual(request.time, 0.181)

        self.assertEqual(logan.parse_log_line(a2), None)
        self.assertEqual(logan.parse_log_line(a3), None)

    def test_process_log_stream(self):
        stream = [logan.RequestInfo('/v1', 0.1),
                  logan.RequestInfo('/v2', 0.2),
                  logan.RequestInfo('/v2', 0.3),
                  logan.RequestInfo('/v3', 0.4),
                  logan.RequestInfo('/v1', 0.2),
                  None]

        data = logan.process_log_stream(stream, 0.5)
        self.assertEqual(data.total_count, 5)
        self.assertEqual(len(data.data), 3)

        internal_data = sorted(data.data, key=lambda x: x['url'])
        self.assertEqual(internal_data[0]['url'], '/v1')
        self.assertEqual(len(internal_data[0]['times']), 2)
        self.assertAlmostEqual(internal_data[0]['time_sum'], 0.3)

    def test_process_log_stream_threshold(self):
        stream = [logan.RequestInfo('/v1', 0.1),
                  None, None]
        error = False
        try:
            logan.process_log_stream(stream, 0.6)
        except Exception:
            error = True
        self.assertTrue(error)

    def test_process_log(self):
        """
        Test log processing operations
        """

        data = [
            {'url': '/v1', 'times': [1, 1, 1], 'time_sum': 3},
            {'url': '/v2', 'times': [2, 1, 3], 'time_sum': 6},
            {'url': '/v3', 'times': [1, 0.5, 0.5, 0.5, 1.5], 'time_sum': 4},
        ]
        data = logan.ParsedData(data, 13, 11)
        data = logan.process_data(data, 2)

        self.assertEqual(len(data), 2)

        row = data[0]
        self.assertEqual(row['url'], '/v2')
        self.assertAlmostEqual(row['time_med'], 2)
        self.assertEqual(row['count'], 3)

        res = round(3 * 100 / 11, 3)
        self.assertAlmostEqual(row['count_perc'], res)

        res = round(6 * 100 / 13, 3)
        self.assertAlmostEqual(row['time_perc'], res)

        self.assertAlmostEqual(row['time_max'], 3)
        self.assertAlmostEqual(row['time_avg'], 2)
        self.assertAlmostEqual(row['time_sum'], 6)


if __name__ == '__main__':
    unittest.main()
