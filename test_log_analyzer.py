import unittest
import log_analyzer as logan


class TestLogAnalyzer(unittest.TestCase):

    def test_regex_filename(self):
        """
        Check filename regex correctness
        """
        regex = logan.log_filename_regex()
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
        regex = logan.log_filename_regex()
        self.assertEqual(logan.find_last_log_from_list(regex, log_list), result_file)

    def test_regex_message(self):
        """
        Check message regex correctness
        """
        regex = logan.log_line_regex()
        a1 = '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] "GET /api/v2/banner/7763463 HTTP/1.1" 200 1018 "-"' \
             ' "Configovod" "-" "1498697422-2118016444-4708-9752774" "712e90144abee9" 0.181'
        a2 = '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] "GET /api/v2/banner/7763463 HTTP/1.1" 200 1018 "-"' \
             ' "Configovod" "-" "1498697422-2118016444-4708-9752774" "712e90144abee9" 0181'
        a3 = '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] "GET /api/v2/banner/7763463 HTTP/1.1" 200 1018 "-"' \
             ' "Configovod" "-" "1498697422-2118016444-4708-9752774" "712e90144abee9"0.181'

        match = regex.match(a1)
        self.assertNotEqual(match, None)
        self.assertEqual(match.group('url'), '/api/v2/banner/7763463')
        self.assertEqual(match.group('time'), '0.181')

        match = regex.match(a2)
        self.assertEqual(match, None)

        match = regex.match(a3)
        self.assertEqual(match, None)

    def test_process_log(self):
        """
        Test log processing operations
        """
        log_lines = [
            '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] "GET /api/v1 HTTP/1.1" '
            '200 1018 "-" "Configovod" "-" "1498697422-2118016444-4708-9752774" "712e90144abee9" 0.1',
            '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] "GET /api/v2 HTTP/1.1" '
            '200 1018 "-" "Configovod" "-" "1498697422-2118016444-4708-9752774" "712e90144abee9" 0.25',
            '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] "GET /api/v1 HTTP/1.1" '
            '200 1018 "-" "Configovod" "-" "1498697422-2118016444-4708-9752774" "712e90144abee9" 0.3',
            '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] "GET /api/v2 HTTP/1.1" '
            '200 1018 "-" "Configovod" "-" "1498697422-2118016444-4708-9752774" "712e90144abee9" 0.1',
            '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] "GET /api/v3 HTTP/1.1" '
            '200 1018 "-" "Configovod" "-" "1498697422-2118016444-4708-9752774" "712e90144abee9" 0.125',
            '1.169.137.128 -  - [29/Jun/2017:03:50:23 +0300] "GET /api/v2 HTTP/1.1" '
            '200 1018 "-" "Configovod" "-" "1498697422-2118016444-4708-9752774" "712e90144abee9" 0.5',
        ]

        data = logan.process_log(log_lines, 2, 0.1)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[1]['url'], '/api/v1')
        self.assertAlmostEqual(data[0]['time_sum'], 0.85)
        self.assertAlmostEqual(data[0]['time_med'], 0.25)


if __name__ == '__main__':
    unittest.main()
