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
Document Length:        34 bytes

Concurrency Level:      100
Time taken for tests:   5.718 seconds
Complete requests:      50000
Failed requests:        0
Total transferred:      8950000 bytes
HTML transferred:       1700000 bytes
Requests per second:    8744.85 [#/sec] (mean)
Time per request:       11.435 [ms] (mean)
Time per request:       0.114 [ms] (mean, across all concurrent requests)
Transfer rate:          1528.64 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.1      0       5
Processing:     0   11  14.1      6     146
Waiting:        0   11  14.1      6     146
Total:          0   11  14.1      6     146

Percentage of the requests served within a certain time (ms)
  50%      6
  66%     12
  75%     18
  80%     22
  90%     32
  95%     38
  98%     44
  99%     48
 100%    146 (longest request)

