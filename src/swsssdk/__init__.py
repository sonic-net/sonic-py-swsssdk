"""
Utility library for Switch-state Redis database access and syslog reporting.
"""
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.NullHandler())

try:
    from .dbconnector import SonicDBConfig, SonicV2Connector
    from .configdb import ConfigDBConnector, ConfigDBPipeConnector
    from .sonic_db_dump_load import sonic_db_dump_load
except (KeyError, ValueError):
    msg = "Failed to database connector objects -- incorrect database config schema."
    logger.exception(msg)
    raise RuntimeError(msg)
