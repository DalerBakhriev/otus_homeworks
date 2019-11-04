import datetime
import gzip
import json
import logging
import os
import re
from statistics import median
from string import Template
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    NoReturn,
    Optional,
    Tuple,
    Union
)

from models import Config, LatestLogFile, SingleLogParserResult
from utils import (
    configure_cli_parser,
    configure_logging,
    get_config_parameters
)

CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./nginx_logs",
    "LOG_FILE": "./script_logs/test.log",
    "FAILURES_PERCENT_THRESHOLD": 50.0
}

DATE_FORMAT_IN_LOG_FILE_NAME = "%Y%m%d"
DATE_FORMAT_FOR_REPORT = "%Y.%m.%d"
NUM_SIGNS_FOR_STATS = 3


def find_latest_log(log_dir: str) -> Optional[LatestLogFile]:

    """
    Finds log with latest creation date
    :param log_dir: directory with log files
    :return: LatestLogFile object with information about path, creation date,  file extension
    """

    log_file_pattern = re.compile(r"nginx-access-ui.log-\d{8}.(gz|log|txt)$")
    date_pattern = re.compile(r"\d{8}")
    current_max_date = None
    current_file_name = None

    for file in os.scandir(log_dir):
        log_pattern_matches = re.findall(log_file_pattern, file.name)
        if log_pattern_matches:
            creation_date_as_string = re.search(date_pattern, file.name).group(0)
            creation_date = datetime.datetime.strptime(creation_date_as_string, DATE_FORMAT_IN_LOG_FILE_NAME)

            if current_max_date is None:
                current_max_date = creation_date
                current_file_name = file.name
            elif creation_date > current_max_date:
                current_max_date = creation_date
                current_file_name = file.name

    if current_file_name is not None:
        log_file_path = os.path.join(log_dir, current_file_name)
        _, file_extension = os.path.splitext(log_file_path)
        return LatestLogFile(
            path=log_file_path,
            date_of_creation=current_max_date,
            extension=file_extension
        )


def parse_log_file(log_file: LatestLogFile,
                   log_file_opener: Callable) -> Iterable[SingleLogParserResult]:

    """
    Parses log file line by line
    :param log_file: file with logs to parse
    :param log_file_opener: function to open log file with
    :return: generator of parsing results by line
    """

    with log_file_opener(log_file.path, mode="rt", encoding="Utf-8") as analyzed_log:
        for line_ in analyzed_log:
            line_parsing_is_failed = False
            try:
                logs_line = line_.split()
                url, duration = logs_line[6], float(logs_line[-1])
            except Exception:
                logging.error("Failed parsing line: %s", line_)
                url, duration = None, None
                line_parsing_is_failed = True
            yield SingleLogParserResult(
                url=url,
                time=duration,
                is_failed=line_parsing_is_failed
            )


def generate_report_name(cfg: Config, log_file: LatestLogFile) -> str:

    """
    Generates name for html report
    :param log_file: file with latest log
    :param cfg: application config
    :return: name for report
    """

    log_creation_date = log_file.date_of_creation.strftime(DATE_FORMAT_FOR_REPORT)
    report_name = os.path.join(cfg.report_dir, f"report-{log_creation_date}.html")

    return report_name


def prepare_stats_for_json(
        url_stats: Dict[str, Dict[str, Union[int, float]]]
) -> List[Dict[str, Union[int, float]]]:

    """
    Prepares url stats for rendering template
    :param url_stats: stats by url
    :return:
    """

    url_stats_for_json = list()
    for url in url_stats:
        url_stats[url]["url"] = url
        url_stats_for_json.append(url_stats[url])

    return url_stats_for_json


def calculate_url_stats(
        parsed_line_gen: Iterable[SingleLogParserResult],
        conf: Config
) -> Tuple[Dict[str, Dict[str, Union[int, float]]], float]:

    """
    Calculates url stats for report
    :param parsed_line_gen: generator of parsed lines result
    :param conf application config
    :return: url stats for log file
    """

    num_failures = 0
    num_requests = 0
    all_requests_time = 0
    calculations_by_url = dict()

    for single_line_result in parsed_line_gen:
        if single_line_result.is_failed:
            num_requests += 1
            num_failures += 1
            continue

        curr_url = single_line_result.url

        if curr_url not in calculations_by_url:
            calculations_by_url[curr_url] = {"num_times": 1, "time": [single_line_result.time]}
        else:
            calculations_by_url[curr_url]["num_times"] += 1
            calculations_by_url[curr_url]["time"].append(single_line_result.time)
        num_requests += 1
        all_requests_time += single_line_result.time

    failures_percentage = round(100 * num_failures / num_requests)

    result_by_url = dict()
    for url in calculations_by_url:
        num_times = calculations_by_url[url]["num_times"]
        time_durations = calculations_by_url[url]["time"]
        result_by_url[url] = {
            "count": num_times,
            "count_perc": round(100 * num_times / num_requests, NUM_SIGNS_FOR_STATS),
            "time_sum": round(sum(time_durations), NUM_SIGNS_FOR_STATS),
            "time_perc": round(100 * sum(time_durations) / all_requests_time, NUM_SIGNS_FOR_STATS),
            "time_avg": round(sum(time_durations) / len(time_durations), NUM_SIGNS_FOR_STATS),
            "time_max": round(max(time_durations), NUM_SIGNS_FOR_STATS),
            "time_med": round(median(time_durations), NUM_SIGNS_FOR_STATS)
        }

    url_stats = dict(
        sorted(
            result_by_url.items(),
            key=lambda url_stats_: url_stats_[1]["time_sum"],
            reverse=True
        )[:conf.report_size]
    )

    url_stats_for_json = prepare_stats_for_json(url_stats=url_stats)

    return url_stats_for_json, failures_percentage


def render_report(url_stats_for_json: Dict[str, Dict[str, Union[int, float]]],
                  cfg: Config,
                  report_name: str) -> NoReturn:
    """
    Takes report template and renders report for current log file
    :param url_stats_for_json: url stats for log file
    :param report_name: name of report that will be generated
    :param cfg: application config
    :return:
    """

    report_template = os.path.join(cfg.report_dir, "report.html")
    with open(report_template, "rt", encoding="utf-8") as report_template:
        template_html = report_template.read()

    prepared_url_stats = json.dumps(url_stats_for_json)
    fulfilled_template = Template(template_html).safe_substitute(table_json=prepared_url_stats)

    with open(report_name, "w", encoding="utf-8") as prepared_report:
        prepared_report.write(fulfilled_template)


def generate_report(default_config: Dict[str, Union[int, str]]) -> NoReturn:

    """
    Generates report for the latest nginx log file
    :param default_config: default application config
    :return:
    """

    cli_parser = configure_cli_parser()
    args = cli_parser.parse_args()
    config_file_path = args.config

    conf = get_config_parameters(
        default_config=default_config,
        config_file_path=config_file_path
    )

    configure_logging(path_to_log_file=conf.log_file)

    try:
        logging.info("Trying to find latest log file from directory %s", conf.log_dir)
        latest_log_file = find_latest_log(log_dir=conf.log_dir)
        logging.info("Latest log file is %s", latest_log_file.path)

        logging.info("Generating report name for log file: %s", latest_log_file.path)
        report_name = generate_report_name(cfg=conf, log_file=latest_log_file)
        logging.info("Report name is %s", report_name)

        if os.path.exists(report_name):
            logging.info("Report for this log is already done")
            return

        if latest_log_file is None:
            logging.info("No log file to generate report for")
            return

        log_file_opener = gzip.open if latest_log_file.extension == ".gz" else open

        logging.info("Started to parse log file: %s", latest_log_file.path)
        parsed_line_gen = parse_log_file(log_file=latest_log_file, log_file_opener=log_file_opener)

        logging.info("Started to calculate stats for url from file: %s", latest_log_file.path)
        url_stats_for_report, failures_percent = calculate_url_stats(parsed_line_gen=parsed_line_gen, conf=conf)
        logging.info("Successfully calculated stats by url from file: %s", latest_log_file.path)

        if failures_percent > conf.failures_percent_threshold:
            logging.error(
                "Percent of failures during line parsing is %f, threshold is %f. Limit exceeded.",
                failures_percent,
                conf.failures_percent_threshold
            )
            return

        logging.info("Rendering template for report %s", report_name)
        render_report(url_stats_for_json=url_stats_for_report,
                      cfg=conf,
                      report_name=report_name)
        logging.info("Successfully generated report %s", report_name)

    except Exception:
        logging.exception("Something went wrong during generating report")


if __name__ == "__main__":
    cnt = 0
    with gzip.open("./nginx_logs/nginx-access-ui.log-20170630.gz", "rt", encoding="utf-8") as f:
        with open("./nginx_logs/test_sample.txt", "w", encoding="utf-8") as f2:
            for line in f:
                f2.write(line)
                cnt += 1
                if cnt == 1000:
                    break

