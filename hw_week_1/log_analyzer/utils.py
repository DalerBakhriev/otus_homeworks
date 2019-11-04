import json
import logging
from argparse import ArgumentParser
from typing import Dict, Union, Optional

from models import Config


def configure_cli_parser() -> ArgumentParser:

    """
    Configures argument parser to make the app working like CLI
    :return: object which will parse the arguments from command line
    """

    parser = ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default="./config.json",
        help="Path to config file"
    )

    return parser


def parse_config_file(path: str) -> Dict[str, Union[int, str]]:

    """
    Parses optional config file
    :param path: path to file with config
    :return: dictionary with config parameters
    """

    with open(path, "rt") as config_file:
        config_from_file = json.load(config_file)

    return config_from_file


def get_config_parameters(default_config: Dict[str, Union[int, str]],
                          config_file_path: str) -> Optional[Config]:

    """
    Parse config parameters such as
    :param default_config: dictionary with default config parameters
    :param config_file_path: path to optional config file
    :return: final config after merging config from file and default config with priority on file config
    """

    config_from_file = parse_config_file(path=config_file_path)

    final_config = dict()
    for conf_param in default_config:
        if conf_param in config_from_file:
            final_config[conf_param] = config_from_file[conf_param]
        else:
            final_config[conf_param] = default_config.get(conf_param, None)

    return Config(
        report_size=final_config["REPORT_SIZE"],
        report_dir=final_config["REPORT_DIR"],
        log_dir=final_config["LOG_DIR"],
        log_file=final_config["LOG_FILE"],
        failures_percent_threshold=final_config["FAILURES_PERCENT_THRESHOLD"]
    )


def configure_logging(path_to_log_file: Optional[str]):

    """
    Configures app logging
    :param path_to_log_file: path to write log file
    :return:
    """

    logging.basicConfig(
        filename=path_to_log_file,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
        level=logging.INFO
    )
