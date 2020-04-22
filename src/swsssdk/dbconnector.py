"""
Database connection module for SwSS
"""
from . import logger
from .interface import DBInterface
import os
import json

# FIXME: Convert to metaclasses when Py2 support is removed. Metaclasses have unique interfaces to Python2/Python3.

class SonicDBConfig(object):
    SONIC_DB_GLOBAL_CONFIG_FILE = "/var/run/redis/sonic-db/database_global.json"
    SONIC_DB_CONFIG_FILE = "/var/run/redis/sonic-db/database_config.json"
    _sonic_db_config_dir = "/var/run/redis/sonic-db"
    _sonic_db_global_config_init = False
    _sonic_db_config_init = False
    _sonic_db_config = {}

    """This is the database_global.json parse and load API. This file has the namespace name and
       the corresponding database_config.json file. The global file is significant for the
       applications running in the linux host namespace, like eg: config/show cli, snmp etc which
       needs to connect to databases running in other namespaces. If the "namespace" attribute is not
       specified for an "include" attribute, it refers to the linux host namespace.
       If the user passes namespace parameter, this API loads json file for that namespace alone.
    """
    @staticmethod
    def load_sonic_global_db_config(global_db_file_path=SONIC_DB_GLOBAL_CONFIG_FILE, namespace=None):
        """
        Parse and load the global database config json file
        """
        if SonicDBConfig._sonic_db_global_config_init == True:
            return

        if os.path.isfile(global_db_file_path) ==  True:
            global_db_config_dir = os.path.dirname(global_db_file_path)
            with open(global_db_file_path, "r") as read_file:
                all_ns_dbs = json.load(read_file)
                for entry in all_ns_dbs['INCLUDES']:
                    if 'namespace' not in entry.keys():
                        # If the user already invoked load_sonic_db_config() explicitly to load the
                        # database_config.json file for current namesapce, skip loading the file
                        # referenced here in the global config file.
                        if SonicDBConfig._sonic_db_config_init == True:
                            continue
                        ns = ''
                    else:
                        ns = entry['namespace']

                    # If API is called with a namespace parameter, load the json file only for that namespace.
                    if namespace is not None and  ns != namespace:
                        continue;

                    # Check if _sonic_db_config already have this namespace present
                    if ns in SonicDBConfig._sonic_db_config:
                        msg = "The database_config for this namespace '{}' is already parsed. !!".format(ns)
                        logger.warning(msg)
                        continue

                    db_include_file = os.path.join(global_db_config_dir, entry['include'])

                    # Not finding the database_config.json file for the namespace
                    if os.path.isfile(db_include_file) == False:
                        msg = "'{}' file is not found !!".format(db_include_file)
                        logger.warning(msg)
                        continue

                    # As we load the database_config.json file for current namesapce,
                    # set the _sonic_db_config_init flag to True to prevent loading again
                    # by the API load_sonic_db_config()
                    if ns is '':
                        SonicDBConfig._sonic_db_config_init = True

                    with open(db_include_file, "r") as inc_file:
                        SonicDBConfig._sonic_db_config[ns] = json.load(inc_file)

                    # If API is called with a namespace parameter,we break here as we loaded the json file.
                    if namespace is not None and  ns == namespace:
                        break;

        SonicDBConfig._sonic_db_global_config_init = True

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
                # The database_config.json is loaded with '' as key. This refers to the local namespace.
                SonicDBConfig._sonic_db_config[''] = json.load(read_file)
        except (OSError, IOError):
            msg = "Could not open sonic database config file '{}'".format(sonic_db_file_path)
            logger.exception(msg)
            raise RuntimeError(msg)
        SonicDBConfig._sonic_db_config_init = True

    @staticmethod
    def namespace_validation(namespace):
        # Check the namespace is valid.
        if namespace is None:
            msg = "invalid namespace name given as input"
            logger.warning(msg)
            raise RuntimeError(msg)

        # Check if the global config is loaded entirely or for the namespace
        if namespace != '' and SonicDBConfig._sonic_db_global_config_init == False:
            msg = "Load the global DB config first using API load_sonic_global_db_config"
            logger.warning(msg)
            raise RuntimeError(msg)

        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()

        if namespace not in SonicDBConfig._sonic_db_config:
            msg = "{} is not a valid namespace name in configuration file".format(namespace)
            logger.warning(msg)
            raise RuntimeError(msg)

    @staticmethod
    def EMPTY_NAMESPACE(ns):
        if ns is None:
            return ''
        else:
            return ns

    @staticmethod
    def db_name_validation(db_name, namespace=None):
        namespace = SonicDBConfig.EMPTY_NAMESPACE(namespace)
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.namespace_validation(namespace)
        db=SonicDBConfig._sonic_db_config[namespace]["DATABASES"]
        if db_name not in db:
            msg = "{} is not a valid database name in configuration file".format(db_name)
            logger.warning(msg)
            raise RuntimeError(msg)

    @staticmethod
    def inst_name_validation(inst_name, namespace=None):
        namespace = SonicDBConfig.EMPTY_NAMESPACE(namespace)
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.namespace_validation(namespace)
        instances = SonicDBConfig._sonic_db_config[namespace]["INSTANCES"]
        if inst_name not in instances:
            msg = "{} is not a valid instance name in configuration file".format(inst_name)
            logger.warning(msg)
            raise RuntimeError(msg)

    @staticmethod
    def get_dblist(namespace=None):
        namespace = SonicDBConfig.EMPTY_NAMESPACE(namespace)
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.namespace_validation(namespace)
        return SonicDBConfig._sonic_db_config[namespace]["DATABASES"].keys()

    @staticmethod
    def get_ns_list():
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        return SonicDBConfig._sonic_db_config.keys()

    @staticmethod
    def get_instance(db_name, namespace=None):
        namespace = SonicDBConfig.EMPTY_NAMESPACE(namespace)
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.db_name_validation(db_name, namespace)
        inst_name = SonicDBConfig._sonic_db_config[namespace]["DATABASES"][db_name]["instance"]
        SonicDBConfig.inst_name_validation(inst_name, namespace)
        return SonicDBConfig._sonic_db_config[namespace]["INSTANCES"][inst_name]

    @staticmethod
    def get_instancelist(namespace=None):
        namespace = SonicDBConfig.EMPTY_NAMESPACE(namespace)
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.namespace_validation(namespace)
        return SonicDBConfig._sonic_db_config[namespace]["INSTANCES"]

    @staticmethod
    def get_socket(db_name, namespace=None):
        namespace = SonicDBConfig.EMPTY_NAMESPACE(namespace)
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        return SonicDBConfig.get_instance(db_name, namespace)["unix_socket_path"]

    @staticmethod
    def get_hostname(db_name, namespace=None):
        namespace = SonicDBConfig.EMPTY_NAMESPACE(namespace)
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        return SonicDBConfig.get_instance(db_name, namespace)["hostname"]

    @staticmethod
    def get_port(db_name, namespace=None):
        namespace = SonicDBConfig.EMPTY_NAMESPACE(namespace)
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        return SonicDBConfig.get_instance(db_name, namespace)["port"]

    @staticmethod
    def get_dbid(db_name, namespace=None):
        namespace = SonicDBConfig.EMPTY_NAMESPACE(namespace)
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.db_name_validation(db_name, namespace)
        return SonicDBConfig._sonic_db_config[namespace]["DATABASES"][db_name]["id"]

    @staticmethod
    def get_separator(db_name, namespace=None):
        namespace = SonicDBConfig.EMPTY_NAMESPACE(namespace)
        if SonicDBConfig._sonic_db_config_init == False:
            SonicDBConfig.load_sonic_db_config()
        SonicDBConfig.db_name_validation(db_name, namespace)
        return SonicDBConfig._sonic_db_config[namespace]["DATABASES"][db_name]["separator"]

class SonicV2Connector(DBInterface):
    def __init__(self, use_unix_socket_path=False, namespace=None, **kwargs):
        super(SonicV2Connector, self).__init__(**kwargs)
        self.use_unix_socket_path = use_unix_socket_path

        """If the user don't give the namespace as input, it refers to the local namespace 
           where this application is run. (It could be a network namespace or linux host namesapce)
        """
        self.namespace = namespace

        # The TCP connection to a DB in another namespace in not supported.
        if namespace is not None and use_unix_socket_path == False:
            message = "TCP connectivity to the DB instance in a different namespace is not implemented!"
            raise NotImplementedError(message)

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
        return SonicDBConfig.get_dblist(self.namespace)

    def get_db_instance(self, db_name):
        return SonicDBConfig.get_instance(db_name, self.namespace)

    def get_db_socket(self, db_name):
        return SonicDBConfig.get_socket(db_name, self.namespace)

    def get_db_hostname(self, db_name):
        return SonicDBConfig.get_hostname(db_name, self.namespace)

    def get_db_port(self, db_name):
        return SonicDBConfig.get_port(db_name, self.namespace)

    def get_dbid(self, db_name):
        return SonicDBConfig.get_dbid(db_name, self.namespace)

    def get_db_separator(self, db_name):
        return SonicDBConfig.get_separator(db_name, self.namespace)

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
