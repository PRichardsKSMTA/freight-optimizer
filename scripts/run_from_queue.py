"""Run an optimization item from the queue with structured logging."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import requests


import database.database_functions as dbf
from gui.configuration import ModelConfiguration
from gui.data_configuration.data_filter import DataFilter
from manager import run_from_configuration


def setup_logger() -> logging.Logger:
    """Configure application logging to both stdout and a timestamped file."""

    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"run_from_queue_{timestamp}.log"

    logger = logging.getLogger("run_from_queue")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def main() -> int:
    logger = setup_logger()

    default_param_filename = "scripts/gui/default_params.json"
    gui_configuration_filename = "configurations/gui_configurations.json"

    try:
        logger.info("Loading model configuration files.")
        model_configs = ModelConfiguration(default_param_filename, gui_configuration_filename)
        db_configs = model_configs.get_setting("database_configurations")
    except Exception:
        logger.exception("Failed to load model configurations.")
        return 1

    try:
        logger.info("Connecting to database.")
        con = dbf.get_connection(db_configs)
    except Exception:
        logger.exception("Failed to obtain database connection.")
        return 1

    try:
        logger.info("Fetching next queue item.")
        queue_item = dbf.get_next_queue_item(con)
    except Exception:
        logger.exception("Failed to fetch queue item from database.")
        try:
            con.close()
        except Exception:
            logger.exception("Failed to close database connection after fetch error.")
        return 1

    if not queue_item:
        logger.info("No items in queue.")
        try:
            con.close()
        except Exception:
            logger.exception("Failed to close database connection when no queue items were found.")
            return 1
        return 0

    queue_id = queue_item["QUEUE_ID"]
    client_id = queue_item["CLIENT_ID"]
    scenario_id = queue_item["SCENARIO_ID"]
    run_id = queue_item["RUN_ID"]
    payload = queue_item["PAYLOAD"]

    try:
        logger.info("Marking queue item %s as started.", queue_id)
        dbf.update_queue_item(con, queue_id, start=True)
    except Exception:
        logger.exception("Failed to update queue item %s as started.", queue_id)
        try:
            con.close()
        except Exception:
            logger.exception("Failed to close database connection after start update error.")
        return 1

    try:
        logger.info("Loading scenario %s for client %s.", scenario_id, client_id)
        scenario = dbf.get_scenario(con, scenario_id, client_id)
        data_filter = DataFilter(model_configs.get_setting("database_configurations"), model_configs, client_id=client_id)
        data_filter.load_configuration(scenario_id, scenario=scenario)
    except Exception:
        logger.exception("Failed to load scenario data for queue item %s.", queue_id)
        try:
            dbf.update_queue_item(con, queue_id, start=False)
        except Exception:
            logger.exception("Failed to reset queue item %s after scenario load failure.", queue_id)
        try:
            con.close()
        except Exception:
            logger.exception("Failed to close database connection after scenario load failure.")
        return 1

    model_type = "tsp" if scenario.get("UseTSP") else "two_tour_limit"

    try:
        logger.info("Running optimizer for queue item %s with model type %s.", queue_id, model_type)
        run_from_configuration(
            **{
                "client_id": data_filter.client_id,
                "scenario_id": data_filter.scenario_id,
                "data_filters": data_filter.get_all_filters(),
                "database_configs": model_configs.get_setting("database_configurations"),
                "model_type": model_type,
                "run_id": run_id,
            }
        )
    except Exception:
        logger.exception("Optimizer execution failed for queue item %s.", queue_id)
        try:
            dbf.update_queue_item(con, queue_id, start=False)
        except Exception:
            logger.exception("Failed to reset queue item %s after optimizer failure.", queue_id)
        try:
            con.close()
        except Exception:
            logger.exception("Failed to close database connection after optimizer failure.")
        return 1

    try:
        logger.info("Marking queue item %s as completed.", queue_id)
        dbf.update_queue_item(con, queue_id, start=False)
    except Exception:
        logger.exception("Failed to update queue item %s as completed.", queue_id)
        try:
            con.close()
        except Exception:
            logger.exception("Failed to close database connection after completion update failure.")
        return 1

    url = (
        "https://prod-59.eastus.logic.azure.com:443/workflows/b01dbc3814624f63a70ddb4e9dac90ce/triggers/manual/paths/invoke"
        "?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=xP08IGwZ2r0XNJuMK7_kWz0ez5Hk25hcN5Doi9A44FI"
    )

    try:
        logger.info("Posting webhook for queue item %s.", queue_id)
        json_arg = json.loads(payload)
        response = requests.post(url, json=json_arg, timeout=30)
        response.raise_for_status()
        logger.info("Webhook posted successfully with status code %s.", response.status_code)
    except Exception:
        logger.exception("Failed to post webhook for queue item %s.", queue_id)
        try:
            con.close()
        except Exception:
            logger.exception("Failed to close database connection after webhook failure.")
        return 1

    try:
        con.close()
    except Exception:
        logger.exception("Failed to close database connection after processing queue item %s.", queue_id)
        return 1

    logger.info("Queue item %s processed successfully.", queue_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
