
# Mini Http Server

### Description

Serve static files in ROOT_DIRECTORY. Server uses multithreading model, it creates thread workers 
and pushes accepted connections to common queue. Workers try to get connection from queue and handle it.

Supports:
* HEAD
* GET

### Using

Start server with 10 workers and ROOT_DIRECTORY = './' on 12222 port:

```
python3 httpd.py -w 10 -r ./
```

Params:

* -w (--workers) - number of worker threads
* -r (--root_directory) - root dir of static 
* -l (--log) - log file
* -c (--config) (default config.json) - read all configuration from file

Config file: 

```

{
  "root_directory": "./root",
  "workers": 10,
  "port": 80,
  "backlog": 50,
  "log": "http.log"
}

```

additional params in config: 

*  port - port of server
*  backlog - size of backlog queue in socket.listen  


### Benchmarks

#### For 127.0.0.1/

* Server Software:        
* Server Hostname:        127.0.0.1
* Server Port:            80


* Document Path:          /
* Document Length:        0 bytes


* Concurrency Level:      100
* Time taken for tests:   12.625 seconds
* Complete requests:      50000
* Failed requests:        0
* Non-2xx responses:      50000
* Total transferred:      1300000 bytes
* HTML transferred:       0 bytes
* Requests per second:    3960.47 [#/sec] (mean)
* Time per request:       25.250 [ms] (mean)
* Time per request:       0.252 [ms] (mean, across all concurrent requests)
* Transfer rate:          100.56 [Kbytes/sec] received

Connection Times (ms)

|              | min  | mean | [+/-sd] | median |  max |
|--------------|------|------|---------|--------|------|
| Connect:     |  0   |  0   | 21.7    |  0     | 1012 |
| Processing:  |  9   | 25   | 6.1     | 24     |  124 |
| Waiting:     |  8   | 25   | 6.1     | 24     |  123 |
| Total:       |  13  | 25   | 22.5    | 24     | 1036 |

Percentage of the requests served within a certain time (ms)

|      |       |
|------|-------|
|  50% |    24 |
|  66% |    24 |
|  75% |    25 |
|  80% |    25 |
|  90% |    26 |
|  95% |    27 |
|  98% |    30 |
|  99% |    36 |
| 100% |  1036 |


#### For 127.0.0.1/httptest/wikipedia_russia.html

Finished 50000 requests


* Server Software:        MiniServerForOtus
* Server Hostname:        127.0.0.1
* Server Port:            80


* Document Path:          /httptest/wikipedia_russia.html
* Document Length:        954824 bytes


* Concurrency Level:      100
* Time taken for tests:   29.599 seconds
* Complete requests:      50000
* Failed requests:        0
* Total transferred:      47749000000 bytes
* HTML transferred:       47741200000 bytes
* Requests per second:    1689.25 [#/sec] (mean)
* Time per request:       59.198 [ms] (mean)
* Time per request:       0.592 [ms] (mean, across all concurrent requests)
* Transfer rate:          1575386.36 [Kbytes/sec] received



Connection Times (ms)

|             |   min | mean | [+/-sd] | median |   max  |
|-------------|-------|------|---------|--------|--------|
| Connect:    |   0   | 1    | 26.4    |   0    | 1028   |
| Processing: |   17  | 58   | 5.0     |  57    |  98    |
| Waiting:    |   17  | 58   | 5.0     |  57    |  98    |
| Total:      |   22  | 59   | 26.9    |  57    |   1101 |

Percentage of the requests served within a certain time (ms)

|       |       |
|-------|-------|
|  50%  |   57  |
|  66%  |   59  |
|  75%  |   59  |
|  80%  |   60  |
|  90%  |   64  |
|  95%  |   70  |
|  98%  |   74  |
|  99%  |   76  |
| 100%  | 1101  |

