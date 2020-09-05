import os
import gzip
import sys
import glob
import logging
import argparse
# brew install protobuf
# protoc  --python_out=. ./appsinstalled.proto
# pip install protobuf
import appsinstalled_pb2
# pip install python-memcached
import memcache
from typing import List, NamedTuple, Optional

NORMAL_ERR_RATE = 0.01


class AppsInstalled(NamedTuple):

    dev_type: str
    dev_id: str
    lat: float
    lon: float
    apps: List[int]


def dot_rename(path: str) -> None:
    head, fn = os.path.split(path)
    # atomic in most cases
    os.rename(path, os.path.join(head, "." + fn))


def insert_apps_installed(memcached_address: str,
                          apps_installed: AppsInstalled,
                          dry_run: bool = False) -> bool:

    user_apps = appsinstalled_pb2.UserApps()
    user_apps.lat = apps_installed.lat
    user_apps.lon = apps_installed.lon
    key = f"{apps_installed.dev_type}:{apps_installed.dev_id}"
    user_apps.apps.extend(apps_installed.apps)
    packed = user_apps.SerializeToString()
    # @TODO persistent connection
    # @TODO retry and timeouts!
    try:
        if dry_run:
            logging.debug("%s - %s -> %s" % (memcached_address, key, str(user_apps).replace("\n", " ")))
        else:
            memcached = memcache.Client([memcached_address])
            memcached.set(key, packed)
    except Exception as e:
        logging.exception("Cannot write to memcached %s: %s" % (memcached_address, e))
        return False

    return True


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
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.isidigit()]
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


def main(arguments):

    device_memcached = {
        "idfa": arguments.idfa,
        "gaid": arguments.gaid,
        "adid": arguments.adid,
        "dvid": arguments.dvid,
    }

    for file_name in glob.iglob(arguments.pattern):
        
        processed = errors = 0
        logging.info("Processing %s" % file_name)
        file_descriptor = gzip.open(file_name)

        for line in file_descriptor:
            line = line.decode("utf-8").strip()
            if not line:
                continue
            apps_installed = parse_apps_installed(line)
            if not apps_installed:
                errors += 1
                continue
            memcached_addr = device_memcached.get(apps_installed.dev_type)
            if not memcached_addr:
                errors += 1
                logging.error("Unknown device type: %s" % apps_installed.dev_type)
                continue
            ok = insert_apps_installed(memcached_addr, apps_installed, arguments.dry)
            if ok:
                processed += 1
            else:
                errors += 1
        if not processed:
            file_descriptor.close()
            dot_rename(file_name)
            continue

        err_rate = float(errors) / processed
        if err_rate < NORMAL_ERR_RATE:
            logging.info("Acceptable error rate (%s). Successfully load" % err_rate)
        else:
            logging.error("High error rate (%s > %s). Failed load" % (err_rate, NORMAL_ERR_RATE))
        file_descriptor.close()
        dot_rename(file_name)


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

    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("-t", "--test", action="store_true", default=False)
    argument_parser.add_argument("-l", "--log", action="store", default=None)
    argument_parser.add_argument("--dry", action="store_true", default=False)
    argument_parser.add_argument("--pattern", action="store", default="/data/appsinstalled/*.tsv.gz")
    argument_parser.add_argument("--idfa", action="store", default="127.0.0.1:33013")
    argument_parser.add_argument("--gaid", action="store", default="127.0.0.1:33014")
    argument_parser.add_argument("--adid", action="store", default="127.0.0.1:33015")
    argument_parser.add_argument("--dvid", action="store", default="127.0.0.1:33016")
    args = argument_parser.parse_args()
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
