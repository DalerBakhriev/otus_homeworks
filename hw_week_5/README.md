# Асинхронный веб сервер с использованием epoll.

Сервер можно запустить со следующими опциями:
- **-w или --workers** - число воркеров (по умолчанию 4)
- **-r или --root** - DOCUMENT_ROOT (по умолчанию текущий каталог)
- **--h или --host** - хост (по умолчанию localhost)
- **-p или --port** - номер порта (по умолчанию 8080)
- **-l или --connections-limit** - максимальное количество соединений в очереди на обработку (по умолчанию 1000)
- **-d или --debug** - включение уровня логирования `debug`


Результаты нагрузочного тестирования:
```sh
$ ab -n 50000 -c 100 -r http://localhost:8080/

Server Software:        Daler.Bakhriev
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        0 bytes

Concurrency Level:      200
Time taken for tests:   3.895 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      5350000 bytes
HTML transferred:       0 bytes
Requests per second:    12835.40 [#/sec] (mean)
Time per request:       15.582 [ms] (mean)
Time per request:       0.078 [ms] (mean, across all concurrent requests)
Transfer rate:          1341.20 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    5  67.5      0    3025
Processing:     3   10   7.1     10     424
Waiting:        3   10   7.1     10     424
Total:          3   14  70.0     10    3039

Percentage of the requests served within a certain time (ms)
  50%     10
  66%     11
  75%     12
  80%     12
  90%     13
  95%     14
  98%     16
  99%     25
 100%   3039 (longest request)
