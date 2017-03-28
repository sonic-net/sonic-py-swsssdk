"""
Utility library for Switch-state Redis database access and syslog reporting.
"""
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.NullHandler())

import json
import os


def _load_connector_map():
    """
    Get database map from the packaged config.
    """
    global _connector_map
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'database.json')

    try:
        with open(db_file, 'r') as f:
            _connector_map = json.load(f)
    except (OSError, IOError):
        # Missing configuration means we can't configure the database index. Fatal error.
        msg = "Could not open database index '{}'".format(db_file)
        logger.exception(msg)
        raise RuntimeError(msg)


_connector_map = {}
_load_connector_map()

try:
    from .dbconnector import SonicV1Connector, SonicV2Connector
except (KeyError, ValueError):
    msg = "Failed to database connector objects -- incorrect database config schema."
    logger.exception(msg)
    raise RuntimeError(msg)
