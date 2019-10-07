"""
Database connection module for SwSS
"""
from . import _connector_map, logger
from .interface import DBInterface


# FIXME: Convert to metaclasses when Py2 support is removed. Metaclasses have unique interfaces to Python2/Python3.

class SonicV2Connector(DBInterface):
    def __init__(self, **kwargs):
        super(SonicV2Connector, self).__init__(**kwargs)

    pass


SonicV2Connector.db_map = _connector_map[SonicV2Connector.__name__]['db_map']

if len(SonicV2Connector.db_map) != len({v['db'] for k, v in SonicV2Connector.db_map.items()}):
    raise RuntimeError("Duplicate DB index detected in configuration.")
