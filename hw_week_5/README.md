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

Concurrency Level:      100
Time taken for tests:   3.969 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      5350000 bytes
HTML transferred:       0 bytes
Requests per second:    12598.74 [#/sec] (mean)
Time per request:       7.937 [ms] (mean)
Time per request:       0.079 [ms] (mean, across all concurrent requests)
Transfer rate:          1316.47 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.4      0      12
Processing:     3    8   3.1      7      45
Waiting:        3    8   3.1      7      45
Total:          4    8   3.1      7      45

Percentage of the requests served within a certain time (ms)
  50%      7
  66%      9
  75%     10
  80%     10
  90%     11
  95%     12
  98%     13
  99%     15
 100%     45 (longest request)

