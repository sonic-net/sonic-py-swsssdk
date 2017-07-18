"""
SONiC ConfigDB connection module 

Example:
    # Write to config DB
    config_db = ConfigDBConnector()
    config_db.connect()
    config_db.set_entry('BGP_NEIGHBOR', '10.0.0.1', {
        'admin_status': state
        })

    # Daemon to watch config change in certain table:
    config_db = ConfigDBConnector()
    handler = lambda table, key, data: print (key, data)
    config_db.add_handler('BGP_NEIGHBOR', handler)
    config_db.connect()
    config_db.listen()

"""

from .dbconnector import SonicV2Connector

class ConfigDBConnector(SonicV2Connector):

    def __init__(self):
        # Connect to Redis through TCP, which does not requires root.
        super(ConfigDBConnector, self).__init__(host='127.0.0.1')
        self.handlers = {}

    def connect(self):
        SonicV2Connector.connect(self, self.CONFIG_DB, False)

    def add_handler(self, table, handler):
        """Add a handler to handle config change in certain table.
        Note that a single handler can be registered to different tables by 
        calling this fuction multiple times.
        Args:
            table: Table name.
            handler: a handler function that has signature of handler(table_name, key, data)
        """
        if not self.handlers.has_key(table):
            self.handlers[table] = set()
        self.handlers[table].add(handler)

    def remove_handler(self, table, handler):
        """Remove a registered handler from a certain table.
        Args:
            table: Table name.
            handler: registered handler.
        Raises:
            ValueError: when the handler provided is not registered to the table.
        """
        if not self.handlers.has_key(table):
            raise ValueError("Handler is not binding to this table.")
        try:
            self.handlers[table].remove(handler)
        except:
            raise ValueError("Handler is not binding to this table.")
        if len(self.handlers[table]) == 0:
            self.handlers.pop(table, None)

    def __fire(self, table, key, data):
        if self.handlers.has_key(table):
            for handlers in self.handlers[table]:
                handlers(table, key, data)

    def listen(self):
        """Start listen Redis keyspace events and will trigger corresponding handlers when content of a table changes.
        """
        self.pubsub = self.redis_clients[self.CONFIG_DB].pubsub()
        self.pubsub.psubscribe("__keyspace@{}__:*".format(self.db_map[self.CONFIG_DB]['db']))
        for item in self.pubsub.listen():
            if item['type'] == 'pmessage':
                _hash = item['channel'].split(':', 1)[1]
                table = _hash.split(':', 1)[0]
                key = _hash.split(':', 1)[1]
                if self.handlers.has_key(table):
                    client = self.redis_clients[self.CONFIG_DB]
                    data = client.hgetall(_hash)
                    self.__fire(table, key, data)

    def set_entry(self, table, key, data):
        """Write a table entry to config db.
        Args:
            table: Table name.
            key: Key of table entry.
            data: Table row data in a form of dictionary {'column_key': 'value', ...}
        """
        client = self.redis_clients[self.CONFIG_DB]
        _hash = '{}:{}'.format(table.upper(), key)
        client.hmset(_hash, data)

    def get_entry(self, table, key):
        """Read a table entry from config db.
        Args:
            table: Table name.
            key: Key of table entry.
        Returns: 
            Table row data in a form of dictionary {'column_key': 'value', ...}
            Empty dictionary if table does not exist or entry does not exist.
        """
        client = self.redis_clients[self.CONFIG_DB]
        _hash = '{}:{}'.format(table.upper(), key)
        return client.hgetall(_hash)

    def get_table(self, table):
        """Read an entire table from config db.
        Args:
            table: Table name.
        Returns: 
            Table data in a dictionary form of 
            { 'row_key': {'column_key': 'value', ...}, ...}
            Empty dictionary if table does not exist.
        """
        client = self.redis_clients[self.CONFIG_DB]
        pattern = '{}:*'.format(table.upper())
        keys = client.keys(pattern)
        data = {}
        for key in keys:
            data[key.split(':')[1]] = client.hgetall(key)
        return data

    def set_config(self, data):
        """Write multiple tables into config db. 
        Args:
            data: config data in a dictionary form
            { 
                'TABLE_NAME': { 'row_key': {'column_key': 'value', ...}, ...},
                ...
            }
        """
        for table_name in data:
            table_data = data[table_name]
            for key in table_data:
                self.set_entry(table_name, key, table_data[key])

    def get_config(self):
        """Read all config data. 
        Returns:
            Config data in a dictionary form of 
            { 
                'TABLE_NAME': { 'row_key': {'column_key': 'value', ...}, ...},
                ...
            }
        """
        client = self.redis_clients[self.CONFIG_DB]
        hashes = client.keys('*')
        data = {}
        for _hash in hashes:
            table_name = _hash.split(':', 1)[0]
            key = _hash.split(':', 1)[1]
            if not data.has_key(table_name):
                data[table_name] = {}
            data[table_name][key] = client.hgetall(_hash)
        return data
        self.pubsub = self.redis_clients[self.CONFIG_DB].pubsub()
        self.pubsub.psubscribe("__keyspace@{}__:*".format(self.db_map[self.CONFIG_DB]['db']))
