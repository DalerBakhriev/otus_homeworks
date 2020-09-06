import os
import gzip
import sys
import glob
import logging
import argparse
import threading
import queue
import multiprocessing as mp
# brew install protobuf
# protoc  --python_out=. ./appsinstalled.proto
# pip install protobuf
import appsinstalled_pb2
# pip install python-memcached
import memcache
from functools import wraps
from typing import (
    Callable, Dict, List,
    NamedTuple, Optional, Tuple
)

NORMAL_ERR_RATE = 0.01
MAX_CHUNK_SIZE = 100
QUEUE_TIMEOUT_SECONDS = 1
STOP_SIGNAL_FOR_THREAD = "stop"


class AppsInstalled(NamedTuple):

    dev_type: str
    dev_id: str
    lat: float
    lon: float
    apps: List[int]


class ProcessResultReport(NamedTuple):

    """
    Named tuple with processing results
    :param num_processed: number of successfully processed rows
    :param num_errors: number of rows failed to process
    """

    num_processed: int
    num_errors: int


def make_retries(method: Callable) -> Callable:

    """
    Decorator for making auto retries
    for methods of key-value storage
    """

    @wraps(method)
    def wrapper(self, *method_args, **method_kwargs):
        result = None
        try:
            result = method(self, *method_args, **method_kwargs)
        except Exception as exception:
            logging.error("Something went wrong. Retrying...")
            if wrapper.calls >= self.retries_limit:
                raise exception
            wrapper.calls += 1
            self._reset_connection()
            wrapper(self, *method_args, **method_kwargs)
        return result

    wrapper.calls = 0

    return wrapper


class KeyValueStorage:

    def __init__(self, address: str, retries_limit: int, timeout: int, dry_run: bool):

        self.address = address
        self.retries_limit = retries_limit
        self.timeout = timeout
        self.dry_run = dry_run
        self._storage = None
        if not self.dry_run:
            self._connect_to_storage()
    
    def _connect_to_storage(self) -> None:
        self._storage = memcache.Client([self.address], socket_timeout=self.timeout)
    
    def _reset_connection(self) -> None:

        if self.dry_run:
            return

        if not self._storage:
            self._connect_to_storage()
            return

        self._storage.disconnect()
        self._connect_to_storage()
    
    def disconnect(self) -> None:

        if self.dry_run:
            return
        if self._storage:
            self._storage.disconnect_all()
    
    @make_retries
    def set_values(self, chunks: Dict[str, str]) -> ProcessResultReport:

        """
        Saves keys and values
        to memcache storage
        :param chunks: chunks with key-values pairs
        """

        num_processed = num_failed = 0
        for key, packed in chunks.items():
            if self.dry_run:
                logging.debug("%s - %s -> %s" % (self.address, key, packed))
                num_processed += 1
                continue
            try:
                if self._storage:
                    self._storage.set(key, packed)
                    num_processed += 1
                else:
                    num_failed += 1
            except Exception as exc:
                num_failed += 1
        
        return ProcessResultReport(num_processed, num_failed)


class MemcachedUploader(threading.Thread):

    def __init__(self,
                 job_queue: queue.Queue,
                 results_report_queue: queue.Queue,
                 memcached_address: str,
                 retries_limit: int,
                 timeout: int,
                 dry_run: bool):

        super().__init__()
        self.job_queue = job_queue
        self.results_report_queue = results_report_queue
        self.storage = KeyValueStorage(
            address=memcached_address,
            retries_limit=retries_limit,
            timeout=timeout,
            dry_run=dry_run
        )

    def run(self):

        num_processed = num_failed = 0
    
        while True:
            chunks = self.job_queue.get()
            if isinstance(chunks, str) and chunks == STOP_SIGNAL_FOR_THREAD:
                self.storage.disconnect()
                break
            process_result_report: ProcessResultReport = self.storage.set_values(chunks)
            num_processed += process_result_report.num_processed
            num_failed += process_result_report.num_errors
            self.job_queue.task_done()
            self.results_report_queue.put(ProcessResultReport(num_processed, num_failed))


def dot_rename(path: str) -> None:
    head, fn = os.path.split(path)
    # atomic in most cases
    os.rename(path, os.path.join(head, "." + fn))


def prepare_installed_apps_for_serialization(apps_installed: AppsInstalled) -> Tuple:

    """
    Prepares serialized installed apps for serialization to string
    and uploading to memcached
    :param apps_installed: named tuple with information about installed apps
    """

    user_apps = appsinstalled_pb2.UserApps()
    user_apps.lat = apps_installed.lat
    user_apps.lon = apps_installed.lon
    key = f"{apps_installed.dev_type}:{apps_installed.dev_id}"
    user_apps.apps.extend(apps_installed.apps)

    return key, user_apps


def serialize_installed_apps(apps_installed: AppsInstalled) -> Tuple[str, str]:

    key, user_apps = prepare_installed_apps_for_serialization(apps_installed)
    packed_user_apps = user_apps.SerializeToString()

    return key, packed_user_apps


def parse_apps_installed(line: str) -> Optional[AppsInstalled]:

    line_parts = line.strip().split("\t")
    if len(line_parts) < 5:
        return
    dev_type, dev_id, lat, lon, raw_apps = line_parts
    if not dev_type or not dev_id:
        return
    try:
        apps = [int(a.strip()) for a in raw_apps.split(",")]
    except ValueError:
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.isdigit()]
        logging.info("Not all user apps are digits: `%s`" % line)
    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        logging.info("Invalid geo coords: `%s`" % line)

    return AppsInstalled(dev_type=dev_type,
                         dev_id=dev_id,
                         lat=lat,
                         lon=lon,
                         apps=apps)


def handle_single_file(file_path: str,
                       device_memcached: Dict[str, str],
                       timeout: int,
                       max_retries_number: int,
                       dry_run: bool = False) -> str:

    """
    Parses installed apps from single file
    and uploads results to memcached
    :param file_path: str with path to archived file
    :param device_memcached: mappings from dev type to memcache storage address
    :param timeout: timeout for storage connection
    :param max_retries_number: maximum number of retries in case of storage connection failure
    :param dry_run: True if should run dry otherwise False
    :return name of uploaded file
    """

    uploading_threads: Dict[str, MemcachedUploader] = {}
    uploading_queues: Dict[str, queue.Queue] = {}
    result_stats_queue: queue.Queue = queue.Queue()

    for storage_id, memcached_address in device_memcached.items():
        uploading_queue: queue.Queue = queue.Queue()
        uploading_thread = MemcachedUploader(
            job_queue=uploading_queue,
            results_report_queue=result_stats_queue,
            memcached_address=memcached_address,
            timeout=timeout,
            retries_limit=max_retries_number,
            dry_run=dry_run
        )
        uploading_threads[storage_id] = uploading_thread
        uploading_queues[storage_id] = uploading_queue
        uploading_thread.start()
    
    chunks: Dict[str, Dict[str, str]] = {}

    num_processed = num_errors = 0
    with gzip.open(file_path) as file_descriptor:

        for line in file_descriptor:
            line = line.decode("utf-8").strip()
            if not line:
                continue
            apps_installed = parse_apps_installed(line)
            if not apps_installed:
                num_errors += 1
                continue
            memcached_addr = device_memcached.get(apps_installed.dev_type)
            if not memcached_addr:
                num_errors += 1
                logging.error("Unknown device type: %s" % apps_installed.dev_type)
                continue

            key, packed_user_apps = serialize_installed_apps(apps_installed)
            chunk = chunks.get(apps_installed.dev_type, {})
            chunk[key] = packed_user_apps
            chunks[apps_installed.dev_type] = chunk

            if len(chunks[apps_installed.dev_type]) == MAX_CHUNK_SIZE:
                uploading_queues[apps_installed.dev_type].put(chunk)
                chunks[apps_installed.dev_type] = {}

        for left_dev_type_chunk in chunks:
            if left_chunk := chunks[left_dev_type_chunk]:
                uploading_queues[left_dev_type_chunk].put(left_chunk)

    for storage_id in uploading_queues:
        uploading_queues[storage_id].put(STOP_SIGNAL_FOR_THREAD)
    
    for storage_id in uploading_threads:
        uploading_threads[storage_id].join()

    while result_stats_queue.qsize() > 0:
        result_stats = result_stats_queue.get()
        num_processed += result_stats.num_processed
        num_errors += result_stats.num_errors
        result_stats_queue.task_done()

    try:
        err_rate = num_errors / num_processed
    except ZeroDivisionError:
        err_rate = 1

    if err_rate < NORMAL_ERR_RATE:
        logging.info("Acceptable error rate (%s). Successfully load" % err_rate)
    else:
        logging.error("High error rate (%s > %s). Failed load" % (err_rate, NORMAL_ERR_RATE))
    
    return file_path


def main(arguments):

    device_memcached = {
        "idfa": arguments.idfa,
        "gaid": arguments.gaid,
        "adid": arguments.adid,
        "dvid": arguments.dvid,
    }

    for file_name in glob.iglob(arguments.pattern):
        logging.info("File for uploading: %s" % file_name)

    arguments_for_uploading = (
        (file_path, device_memcached, arguments.storage_timeout,
         arguments.storage_max_retries, arguments.dry)
        for file_path in glob.iglob(arguments.pattern)
    )

    with mp.Pool(os.cpu_count()) as pool:
        files_uploaded = pool.starmap(handle_single_file, arguments_for_uploading)
    
    for file in files_uploaded:
        dot_rename(file)


def proto_test():
    sample = "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567,3,7,23\ngaid\t7rfw452y52g2gq4g\t55.55\t42.42\t7423,424"
    for line in sample.splitlines():
        dev_type, dev_id, lat, lon, raw_apps = line.strip().split("\t")
        apps = [int(a) for a in raw_apps.split(",") if a.isdigit()]
        lat, lon = float(lat), float(lon)
        user_apps = appsinstalled_pb2.UserApps()
        user_apps.lat = lat
        user_apps.lon = lon
        user_apps.apps.extend(apps)
        packed = user_apps.SerializeToString()
        unpacked = appsinstalled_pb2.UserApps()
        unpacked.ParseFromString(packed)
        assert user_apps == unpacked


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-t", "--test", action="store_true", default=False)
    arg_parser.add_argument("-l", "--log", action="store", default=None)
    arg_parser.add_argument("--dry", action="store_true", default=False)
    arg_parser.add_argument("--pattern", action="store", default="/data/appsinstalled/*.tsv.gz")
    arg_parser.add_argument("--idfa", action="store", default="127.0.0.1:33013")
    arg_parser.add_argument("--gaid", action="store", default="127.0.0.1:33014")
    arg_parser.add_argument("--adid", action="store", default="127.0.0.1:33015")
    arg_parser.add_argument("--dvid", action="store", default="127.0.0.1:33016")
    arg_parser.add_argument("--storage-timeout", type=int, action="store", default=3,
                            help="Timeout for storage connection in seconds")
    arg_parser.add_argument("--storage-max-retries", type=int, action="store", default=3,
                            help="Maximum retries number in case of failed saving")

    args = arg_parser.parse_args()
    logging.basicConfig(
        filename=args.log,
        level=logging.INFO if not args.dry else logging.DEBUG,
        format="[%(asctime)s] %(levelname).1s %(message)s", datefmt="%Y.%m.%d %H:%M:%S"
    )
    if args.test:
        proto_test()
        sys.exit(0)

    logging.info("Memcached loader started with options: %s" % args)
    try:
        main(args)
    except Exception as e:
        logging.exception("Unexpected error: %s" % e)
        sys.exit(1)
