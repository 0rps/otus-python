## Scoring api server

Server for getting scoring info

### Using:
#### Tests running


#####Run unittests:

```
    python3 unit_tests.py
```


#####Run integration tests:

To run these tests you must turn on redis on 6379 port


```
    python3 integration_tests.py
```

#####Run end-to-end tests: 

Starts web server on 8080 port and redis on 6379. Flushes redis after starting.

```
    python3 e2e_tests.py
```

#### To run server:

```
    python3 api.py [--log=log_file] [--port=your_port (default is 8080)] [--store=addr:port (example 127.0.0.1:6379)]
```

### Simple request to api

```
    curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"phone": "79175002040", "email": "orps@gmail.ru", "first_name": "Алексей", "last_name": "неизвестный", "birthday": "01.01.1993", "gender": 1}}' http://127.0.0.1:8080/method/
```