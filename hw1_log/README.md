## Log analyzer

Utility for generating reports about url requests from log files.
Generates report `"report-YYYY.MM.dd.html"` from log file `"nginx-access-ui.log-YYYYMMdd[.gz]"`.

#### Using:
##### To run tests:

```
    python3 test_log_analyzer.py
```

##### To run script:

```
    python3 log_analyzer.py [--config=your_config_file]
```

##### Config

If you don't use `--config option`, script read configurations from `'config.json'`.
Configuration file options:

* REPORT_SIZE - number of urls in report
* REPORT_DIR - dir path for target reports
* LOG_DIR - dir path for source log files
* LOG_FILE - path for file for script logging  (can be null)
* ERROR_THRESHOLD - threshold of errors, if part unparsed string in source log file will be more than this number, then script exists with error.
