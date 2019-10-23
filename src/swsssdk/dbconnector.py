"""
Database connection module for SwSS
"""
from . import logger
from .interface import DBInterface
import os
import json

# FIXME: Convert to metaclasses when Py2 support is removed. Metaclasses have unique interfaces to Python2/Python3.

class SonicDBConfig(object):
    SONIC_DB_CONFIG_FILE = "/var/run/redis/sonic-db/database_config.json"
    _sonic_db_config_init = False
    _sonic_db_config = {}

    @staticmethod
    def load_sonic_db_config(sonic_db_file_path=SONIC_DB_CONFIG_FILE):
        """
        Get multiple database config from the database_config.json
        """
        if SonicDBConfig._sonic_db_config_init == True:
            return

        try:
            if os.path.isfile(sonic_db_file_path) == False:
                msg = "'{}' is not found, it is not expected in production devices!!".format(sonic_db_file_path)
                logger.warning(msg)
                sonic_db_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'database_config.json')
            with open(sonic_db_file_path, "r") as read_file:
                SonicDBConfig._sonic_db_config = json.load(read_file)
        except (OSError, IOError):
            msg = "Could not open sonic database config file '{}'".format(sonic_db_file_path)
            logger.exception(msg)
            raise RuntimeError(msg)
        SonicDBConfig._sonic_db_config_init = True

    @staticmethod
    def db_name_validation(db_name):
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        if db_name not in SonicDBConfig._sonic_db_config["DATABASES"]:
            msg = "{} is not a valid database name in configuration file".format(db_name)
            logger.exception(msg)
            raise RuntimeError(msg)

    @staticmethod
    def inst_name_validation(inst_name):
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        if inst_name not in SonicDBConfig._sonic_db_config["INSTANCES"]:
            msg = "{} is not a valid instance name in configuration file".format(inst_name)
            logger.exception(msg)
            raise RuntimeError(msg)

    @staticmethod
    def get_dblist():
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        return SonicDBConfig._sonic_db_config["DATABASES"].keys()

    @staticmethod
    def get_instance(db_name):
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.db_name_validation(db_name)
        inst_name = SonicDBConfig._sonic_db_config["DATABASES"][db_name]["instance"]
        SonicDBConfig.inst_name_validation(inst_name)
        return SonicDBConfig._sonic_db_config["INSTANCES"][inst_name]

    @staticmethod
    def get_socket(db_name):
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.db_name_validation(db_name)
        return SonicDBConfig.get_instance(db_name)["unix_socket_path"]

    @staticmethod
    def get_hostname(db_name):
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.db_name_validation(db_name)
        return SonicDBConfig.get_instance(db_name)["hostname"]

    @staticmethod
    def get_port(db_name):
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.db_name_validation(db_name)
        return SonicDBConfig.get_instance(db_name)["port"]

    @staticmethod
    def get_dbid(db_name):
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.db_name_validation(db_name)
        return SonicDBConfig._sonic_db_config["DATABASES"][db_name]["id"]

    @staticmethod
    def get_separator(db_name):
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.db_name_validation(db_name)
        return SonicDBConfig._sonic_db_config["DATABASES"][db_name]["separator"]

class SonicV2Connector(DBInterface):
    def __init__(self, use_unix_socket_path=False, **kwargs):
        super(SonicV2Connector, self).__init__(**kwargs)
        self.use_unix_socket_path = use_unix_socket_path
        for db_name in self.get_db_list():
            # set a database name as a constant value attribute.
            setattr(self, db_name, db_name)

    def connect(self, db_name, retry_on=True):
        if self.use_unix_socket_path:
            self.redis_kwargs["unix_socket_path"] = self.get_db_socket(db_name)
            self.redis_kwargs["host"] = None
            self.redis_kwargs["port"] = None
        else:
            self.redis_kwargs["host"] = self.get_db_hostname(db_name)
            self.redis_kwargs["port"] = self.get_db_port(db_name)
            self.redis_kwargs["unix_socket_path"] = None
        db_id = self.get_dbid(db_name)
        super(SonicV2Connector, self).connect(db_id, retry_on)

    def close(self, db_name):
        db_id = self.get_dbid(db_name)
        super(SonicV2Connector, self).close(db_id)

    def get_db_list(self):
        return SonicDBConfig.get_dblist()

    def get_db_instance(self, db_name):
        return SonicDBConfig.get_instance(db_name)

    def get_db_socket(self, db_name):
        return SonicDBConfig.get_socket(db_name)

    def get_db_hostname(self, db_name):
        return SonicDBConfig.get_hostname(db_name)

    def get_db_port(self, db_name):
        return SonicDBConfig.get_port(db_name)

    def get_dbid(self, db_name):
        return SonicDBConfig.get_dbid(db_name)

    def get_db_separator(self, db_name):
        return SonicDBConfig.get_separator(db_name)

    def get_redis_client(self, db_name):
        db_id = self.get_dbid(db_name)
        return super(SonicV2Connector, self).get_redis_client(db_id)

    def publish(self, db_name, channel, message):
        db_id = self.get_dbid(db_name)
        return super(SonicV2Connector, self).publish(db_id, channel, message)

    def expire(self, db_name, key, timeout_sec):
        db_id = self.get_dbid(db_name)
        return super(SonicV2Connector, self).expire(db_id, key, timeout_sec)

    def exists(self, db_name, key):
        db_id = self.get_dbid(db_name)
        return  super(SonicV2Connector, self).exists(db_id, key)

    def keys(self, db_name, pattern='*', *args, **kwargs):
        db_id = self.get_dbid(db_name)
        return super(SonicV2Connector, self).keys(db_id, pattern, *args, **kwargs)

    def get(self, db_name, _hash, key, *args, **kwargs):
        db_id = self.get_dbid(db_name)
        return super(SonicV2Connector, self).get(db_id, _hash, key, *args, **kwargs)

    def get_all(self, db_name, _hash, *args, **kwargs):
        db_id = self.get_dbid(db_name)
        return super(SonicV2Connector, self).get_all(db_id, _hash, *args, **kwargs)

    def set(self, db_name, _hash, key, val, *args, **kwargs):
        db_id = self.get_dbid(db_name)
        return super(SonicV2Connector, self).set(db_id, _hash, key, val, *args, **kwargs)

    def delete(self, db_name, key, *args, **kwargs):
        db_id = self.get_dbid(db_name)
        return super(SonicV2Connector, self).delete(db_id, key, *args, **kwargs)

    def delete_all_by_pattern(self, db_name, pattern, *args, **kwargs):
        db_id = self.get_dbid(db_name)
        super(SonicV2Connector, self).delete_all_by_pattern(db_id, pattern, *args, **kwargs)

    pass
