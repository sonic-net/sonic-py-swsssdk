"""
SONiC ConfigDB connection module 

Example:
    # Write to config DB
    config_db = ConfigDBConnector()
    config_db.connect()
    config_db.mod_entry('BGP_NEIGHBOR', '10.0.0.1', {
        'admin_status': state
        })

    # Daemon to watch config change in certain table:
    config_db = ConfigDBConnector()
    handler = lambda table, key, data: print (key, data)
    config_db.subscribe('BGP_NEIGHBOR', handler)
    config_db.connect()
    config_db.listen()

"""
import sys
import time
from .dbconnector import SonicV2Connector

PY3K = sys.version_info >= (3, 0)

class ConfigDBConnector(SonicV2Connector):

    INIT_INDICATOR = 'CONFIG_DB_INITIALIZED'
    TABLE_NAME_SEPARATOR = '|'
    KEY_SEPARATOR = '|'

    def __init__(self, **kwargs):
        # By default, connect to Redis through TCP, which does not requires root.
        if len(kwargs) == 0:
            kwargs['host'] = '127.0.0.1'
        super(ConfigDBConnector, self).__init__(**kwargs)
        self.handlers = {}

    def __wait_for_db_init(self):
        client = self.redis_clients[self.CONFIG_DB]
        pubsub = client.pubsub()
        initialized = client.get(self.INIT_INDICATOR)
        if not initialized:
            pattern = "__keyspace@{}__:{}".format(self.db_map[self.CONFIG_DB]['db'], self.INIT_INDICATOR)
            pubsub.psubscribe(pattern)
            for item in pubsub.listen():
                if item['type'] == 'pmessage':
                    key = item['channel'].split(':', 1)[1]
                    if key == self.INIT_INDICATOR:
                        initialized = client.get(self.INIT_INDICATOR)
                        if initialized:
                            break
            pubsub.punsubscribe(pattern)


    def connect(self, wait_for_init=True, retry_on=False):
        SonicV2Connector.connect(self, self.CONFIG_DB, retry_on)
        if wait_for_init:
            self.__wait_for_db_init()

    def subscribe(self, table, handler):
        """Set a handler to handle config change in certain table.
        Note that a single handler can be registered to different tables by 
        calling this fuction multiple times.
        Args:
            table: Table name.
            handler: a handler function that has signature of handler(table_name, key, data)
        """
        self.handlers[table] = handler

    def unsubscribe(self, table):
        """Remove registered handler from a certain table.
        Args:
            table: Table name.
        """
        if self.handlers.has_key(table):
            self.handlers.pop(table)

    def __fire(self, table, key, data):
        if self.handlers.has_key(table):
            handler = self.handlers[table]
            handler(table, key, data)

    def listen(self):
        """Start listen Redis keyspace events and will trigger corresponding handlers when content of a table changes.
        """
        self.pubsub = self.redis_clients[self.CONFIG_DB].pubsub()
        self.pubsub.psubscribe("__keyspace@{}__:*".format(self.db_map[self.CONFIG_DB]['db']))
        for item in self.pubsub.listen():
            if item['type'] == 'pmessage':
                key = item['channel'].split(':', 1)[1]
                try:
                    (table, row) = key.split(self.TABLE_NAME_SEPARATOR, 1)
                    if self.handlers.has_key(table):
                        client = self.redis_clients[self.CONFIG_DB]
                        data = self.__raw_to_typed(client.hgetall(key))
                        self.__fire(table, row, data)
                except ValueError:
                    pass    #Ignore non table-formated redis entries

    def __raw_to_typed(self, raw_data):
        if raw_data == None:
            return None
        typed_data = {}
        for raw_key in raw_data:
            key = raw_key
            if PY3K:
                key = raw_key.decode('utf-8')

            # "NULL:NULL" is used as a placeholder for objects with no attributes
            if key == "NULL":
                pass
            # A column key with ending '@' is used to mark list-typed table items
            # TODO: Replace this with a schema-based typing mechanism.
            elif key.endswith("@"):
                value = ""
                if PY3K:
                    value = raw_data[raw_key].decode("utf-8").split(',')
                else:
                    value = raw_data[raw_key].split(',')
                typed_data[key[:-1]] = value
            else:
                if PY3K:
                    typed_data[key] = raw_data[raw_key].decode('utf-8')
                else:
                    typed_data[key] = raw_data[raw_key]
        return typed_data

    def __typed_to_raw(self, typed_data):
        if typed_data == None:
            return None
        elif typed_data == {}:
            return { "NULL": "NULL" }
        raw_data = {}
        for key in typed_data:
            value = typed_data[key]
            if type(value) is list:
                raw_data[key+'@'] = ','.join(value)
            else:
                raw_data[key] = value
        return raw_data

    @staticmethod
    def serialize_key(key):
        if type(key) is tuple:
            return ConfigDBConnector.KEY_SEPARATOR.join(key)
        else:
            return key

    @staticmethod
    def deserialize_key(key):
        tokens = key.split(ConfigDBConnector.KEY_SEPARATOR)
        if len(tokens) > 1:
            return tuple(tokens)
        else:
            return key

    def set_entry(self, table, key, data):
        """Write a table entry to config db.
           Remove extra fields in the db which are not in the data.
        Args:
            table: Table name.
            key: Key of table entry, or a tuple of keys if it is a multi-key table.
            data: Table row data in a form of dictionary {'column_key': 'value', ...}.
                  Pass {} as data will create an entry with no column if not already existed.
                  Pass None as data will delete the entry.
        """
        key = self.serialize_key(key)
        client = self.redis_clients[self.CONFIG_DB]
        _hash = '{}{}{}'.format(table.upper(), self.TABLE_NAME_SEPARATOR, key)
        if data == None:
            client.delete(_hash)
        else:
            original = self.get_entry(table, key)
            client.hmset(_hash, self.__typed_to_raw(data))
            for k in [ k for k in original.keys() if k not in data.keys() ]:
                if type(original[k]) == list:
                    k = k + '@'
                client.hdel(_hash, self.serialize_key(k))

    def mod_entry(self, table, key, data):
        """Modify a table entry to config db.
        Args:
            table: Table name.
            key: Key of table entry, or a tuple of keys if it is a multi-key table.
            data: Table row data in a form of dictionary {'column_key': 'value', ...}.
                  Pass {} as data will create an entry with no column if not already existed.
                  Pass None as data will delete the entry.
        """
        key = self.serialize_key(key)
        client = self.redis_clients[self.CONFIG_DB]
        _hash = '{}{}{}'.format(table.upper(), self.TABLE_NAME_SEPARATOR, key)
        if data == None:
            client.delete(_hash)
        else:
            client.hmset(_hash, self.__typed_to_raw(data))

    def get_entry(self, table, key):
        """Read a table entry from config db.
        Args:
            table: Table name.
            key: Key of table entry, or a tuple of keys if it is a multi-key table.
        Returns: 
            Table row data in a form of dictionary {'column_key': 'value', ...}
            Empty dictionary if table does not exist or entry does not exist.
        """
        key = self.serialize_key(key)
        client = self.redis_clients[self.CONFIG_DB]
        _hash = '{}{}{}'.format(table.upper(), self.TABLE_NAME_SEPARATOR, key)
        return self.__raw_to_typed(client.hgetall(_hash))

    def get_table(self, table):
        """Read an entire table from config db.
        Args:
            table: Table name.
        Returns: 
            Table data in a dictionary form of 
            { 'row_key': {'column_key': value, ...}, ...}
            or { ('l1_key', 'l2_key', ...): {'column_key': value, ...}, ...} for a multi-key table.
            Empty dictionary if table does not exist.
        """
        client = self.redis_clients[self.CONFIG_DB]
        pattern = '{}{}*'.format(table.upper(), self.TABLE_NAME_SEPARATOR)
        keys = client.keys(pattern)
        data = {}
        for key in keys:
            try:
                entry = self.__raw_to_typed(client.hgetall(key))
                if entry != None:
                    if PY3K:
                        key = key.decode('utf-8')
                        (_, row) = key.split(self.TABLE_NAME_SEPARATOR, 1)
                        data[self.deserialize_key(row)] = entry
                    else:
                        (_, row) = key.split(self.TABLE_NAME_SEPARATOR, 1)
                        data[self.deserialize_key(row)] = entry
            except ValueError:
                pass    #Ignore non table-formated redis entries
        return data

    def delete_table(self, table):
        """Delete an entire table from config db.
        Args:
            table: Table name.
        """
        client = self.redis_clients[self.CONFIG_DB]
        pattern = '{}{}*'.format(table.upper(), self.TABLE_NAME_SEPARATOR)
        keys = client.keys(pattern)
        data = {}
        for key in keys:
            client.delete(key)

    def mod_config(self, data):
        """Write multiple tables into config db.
           Extra entries/fields in the db which are not in the data are kept.
        Args:
            data: config data in a dictionary form
            { 
                'TABLE_NAME': { 'row_key': {'column_key': 'value', ...}, ...},
                'MULTI_KEY_TABLE_NAME': { ('l1_key', 'l2_key', ...) : {'column_key': 'value', ...}, ...},
                ...
            }
        """
        for table_name in data:
            table_data = data[table_name]
            for key in table_data:
                self.mod_entry(table_name, key, table_data[key])

    def get_config(self):
        """Read all config data. 
        Returns:
            Config data in a dictionary form of 
            { 
                'TABLE_NAME': { 'row_key': {'column_key': 'value', ...}, ...},
                'MULTI_KEY_TABLE_NAME': { ('l1_key', 'l2_key', ...) : {'column_key': 'value', ...}, ...},
                ...
            }
        """
        client = self.redis_clients[self.CONFIG_DB]
        keys = client.keys('*')
        data = {}
        for key in keys:
            try:
                (table_name, row) = key.split(self.TABLE_NAME_SEPARATOR, 1)
                entry = self.__raw_to_typed(client.hgetall(key))
                if entry != None:
                    data.setdefault(table_name, {})[self.deserialize_key(row)] = entry
            except ValueError:
                pass    #Ignore non table-formated redis entries
        return data

