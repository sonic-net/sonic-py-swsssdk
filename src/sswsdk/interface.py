import time
from functools import wraps

import redis
from redis import RedisError

from . import logger
from .exceptions import UnavailableDataError, MissingClientError

BLOCKING_ATTEMPT_ERROR_THRESHOLD = 10
BLOCKING_ATTEMPT_SUPPRESSION = BLOCKING_ATTEMPT_ERROR_THRESHOLD + 5


def blockable(f):
    """
    "blocking" decorator for Redis accessor methods. Wrapped functions that specify kwarg 'blocking'
    will wait for the specified accessor to return with data.::

        class SonicV1Connector:
            @blockable
            def keys(self, db_name):
                # ...

        # call with:
        db = SonicV1Connector()
        # ...
        db.keys('DATABASE', blocking=True)

    """

    @wraps(f)
    def wrapped(inst, db_name, *args, **kwargs):

        blocking = kwargs.pop('blocking', False)
        attempts = 0
        while True:
            try:
                return f(inst, db_name, *args, **kwargs)
            except UnavailableDataError as e:
                if blocking:
                    inst._unavailable_data_handler(db_name, e.data)
                else:
                    return None
            except redis.exceptions.ResponseError:
                """
                A response error indicates that something is fundamentally wrong with the request itself.
                Retrying the request won't pass unless the schema itself changes. In this case, the error
                should be attributed to the application itself. Re-raise the error.
                """
                logger.exception("Bad DB request [{}:{}]{{ {} }}".format(db_name, f.__name__, str(args)))
                raise
            except (redis.exceptions.RedisError, OSError):
                attempts += 1
                inst._connection_error_handler(db_name)
                msg = "DB access failure by [{}:{}]{{ {} }}".format(db_name, f.__name__, str(args))
                if BLOCKING_ATTEMPT_ERROR_THRESHOLD < attempts < BLOCKING_ATTEMPT_SUPPRESSION:
                    # Repeated access failures implies the database itself is unhealthy.
                    logger.exception(msg=msg)
                else:
                    logger.warning(msg=msg)

    return wrapped


class DBRegistry(dict):
    def __getitem__(self, item):
        if item not in self:
            raise MissingClientError("No client connected for db_name '{}'".format(item))
        return dict.__getitem__(self, item)


class DBInterface(object):
    REDIS_HOST = '127.0.0.1'
    """
    SONiC does not use a password-protected database. By default, Redis will only allow connections to unprotected
    DBs over the loopback ip.
    """

    REDIS_PORT = 6379
    """
    SONiC uses the default port.
    """

    REDIS_UNIX_SOCKET_PATH = "/var/run/redis/redis.sock"
    """
    SONiC uses the default unix socket.
    """

    CONNECT_RETRY_WAIT_TIME = 10
    """
    Wait period in seconds before attempting to reconnect to Redis.
    """

    DATA_RETRIEVAL_WAIT_TIME = 3
    """
    Wait period in seconds to wait before attempting to retrieve missing data.
    """

    PUB_SUB_NOTIFICATION_TIMEOUT = 10.0  # seconds
    """
    Time to wait for any given message to arrive via pub-sub.
    """

    PUB_SUB_MAXIMUM_DATA_WAIT = 30.0  # seconds
    """
    Maximum allowable time to wait on a specific pub-sub notification.
    """

    KEYSPACE_PATTERN = '__key*__:*'
    """
    Pub-sub keyspace pattern
    """

    KEYSPACE_EVENTS = 'KEgh'
    """
    In Redis, by default keyspace events notifications are disabled because while not
    very sensible the feature uses some CPU power. Notifications are enabled using
    the notify-keyspace-events of redis.conf or via the CONFIG SET.
    In order to enable the feature a non-empty string is used, composed of multiple characters,
    where every character has a special meaning according to the following table:
    K - Keyspace events, published with __keyspace@<db>__ prefix.
    E - Keyevent events, published with __keyevent@<db>__ prefix.
    g - Generic commands (non-type specific) like DEL, EXPIRE, RENAME, ...
    $ - String commands
    l - List commands
    s - Set commands
    h - Hash commands
    z - Sorted set commands
    x - Expired events (events generated every time a key expires)
    e - Evicted events (events generated when a key is evicted for maxmemory)
    A - Alias for g$lshzxe, so that the "AKE" string means all the events.
    ACS Redis db mainly uses hash, therefore h is selected.
    """

    db_map = dict()

    def __init__(self):

        super(DBInterface, self).__init__()

        # For thread safety as recommended by python-redis
        # Create a separate client for each database
        self.redis_clients = DBRegistry()

        # Create a channel for receiving needed keyspace event
        # notifications for each client
        self.keyspace_notification_channels = DBRegistry()

        for db_name in self.db_map:
            # set a database name as a constant value attribute.
            setattr(self, db_name, db_name)

    @property
    def db_list(self):
        return self.db_map.keys()

    @classmethod
    def get_dbid(cls, db_name):
        """
        :returns the database index by name. None if the name doesn't exist.
        """
        try:
            return cls.db_map[db_name]['db']
        except (KeyError, ValueError):
            return None

    def connect(self, db_name, retry_on=True):
        """
        :param db_name: named database to connect to
        :param retry_on: if ``True`` -- will attempt to connect continuously.
        if ``False``, only one attempt will be made.
        """
        if retry_on:
            self._persistent_connect(db_name)
        else:
            self._onetime_connect(db_name)

    def _onetime_connect(self, db_name):
        """
        Connect to named database.
        """
        db_id = self.get_dbid(db_name)
        if db_id is None:
            raise ValueError("No database ID configured for '{}'".format(db_name))

        kwargs = dict(
            unix_socket_path=self.REDIS_UNIX_SOCKET_PATH
        )
        kwargs.update(self.db_map[db_name])

        client = redis.StrictRedis(**kwargs)

        # Enable the notification mechanism for keyspace events in Redis
        client.config_set('notify-keyspace-events', self.KEYSPACE_EVENTS)
        self.redis_clients[db_name] = client
        self._subscribe_keyspace_notification(db_name, client)

    def _persistent_connect(self, db_name):
        """
        Keep reconnecting to Database 'db_name' until success
        """
        while True:
            try:
                self._onetime_connect(db_name)
                return
            except RedisError:
                t_wait = self.CONNECT_RETRY_WAIT_TIME
                logger.warning("Connecting to DB '{}' failed, will retry in {}s".format(db_name, t_wait))
                self.close(db_name)
                time.sleep(t_wait)

    def close(self, db_name):
        """
        Close all client(s) / keyspace channels.
        :param db_name: DB to disconnect from.
        """
        if db_name in self.redis_clients:
            self.redis_clients[db_name].connection_pool.disconnect()
        if db_name in self.keyspace_notification_channels:
            self.keyspace_notification_channels[db_name].close()

    def _subscribe_keyspace_notification(self, db_name, client):
        """
        Subscribe the chosent client to keyspace event notifications
        """
        pubsub = client.pubsub()
        pubsub.psubscribe(self.KEYSPACE_PATTERN)
        self.keyspace_notification_channels[db_name] = pubsub

    def get_redis_client(self, db_name):
        """
        :param db_name: Name of the DB to query
        :return: The Redis client instance.
        """
        return self.redis_clients[db_name]

    @blockable
    def keys(self, db_name, pattern='*'):
        """
        Retrieve all the keys of DB %db_name
        """
        client = self.redis_clients[db_name]
        keys = client.keys(pattern=pattern)
        if not keys:
            message = "DB '{}' is empty!".format(db_name)
            logger.warning(message)
            raise UnavailableDataError(message, b'hset')
        else:
            return keys

    @blockable
    def get(self, db_name, _hash, key):
        """
        Retrieve the value of Key %key from Hashtable %hash
        in Database %db_name

        Parameter %blocking indicates whether to wait
        when the query fails
        """
        client = self.redis_clients[db_name]
        val = client.hget(_hash, key)
        if not val:
            message = "Key '{}' unavailable in database '{}' - table '{}'".format(key, _hash, db_name)
            logger.warning(message)
            raise UnavailableDataError(message, key)
        else:
            # redis only supports strings. if any item is set to string 'None', cast it back to the appropriate type.
            return None if val == b'None' else val

    @blockable
    def get_all(self, db_name, _hash):
        """
        Get Hashtable %hash from DB %db_name

        Parameter %blocking indicates whether to wait
        if the hashtable has not been created yet
        """
        client = self.redis_clients[db_name]
        table = client.hgetall(_hash)
        if not table:
            message = "Table '{}' does not exist in database '{}'".format(_hash, db_name)
            logger.warning(message)
            raise UnavailableDataError(message, _hash)
        else:
            # redis only supports strings. if any item is set to string 'None', cast it back to the appropriate type.
            return {k: None if v == b'None' else v for k, v in table.items()}

    @blockable
    def set(self, db_name, _hash, key, val):
        """
        Add %(key, val) to Hashtable %hash in DB %db_name
        Parameter %blocking indicates whether to retry in case of failure
        """
        client = self.redis_clients[db_name]
        return client.hset(_hash, key, val)

    def _unavailable_data_handler(self, db_name, data):
        """
        When the queried config is not available in Redis--wait until it is available.
        Two timeouts are at work here:
        1. Notification timeout - how long to wait before giving up on receiving any given pub-sub message.
        2. Max data wait - sswsdk-specific. how long to wait for the data to populate (in absolute time)
        """
        start = time.time()
        logger.debug("Listening on pubsub channel '{}'".format(db_name))
        while time.time() - start < self.PUB_SUB_MAXIMUM_DATA_WAIT:
            msg = self.keyspace_notification_channels[db_name].get_message(timeout=self.PUB_SUB_NOTIFICATION_TIMEOUT)
            if msg is not None and msg.get('data') == data:
                logger.info("'{}' acquired via pub-sub. Unblocking...".format(data, db_name))
                # Wait for a "settling" period before releasing the wait.
                time.sleep(self.DATA_RETRIEVAL_WAIT_TIME)
                return

        logger.warning("No notification for '{}' from '{}' received before timeout.".format(data, db_name))

    def _connection_error_handler(self, db_name):
        """
        In the event Redis is unavailable, close existing connections, and try again.
        """
        logger.warning('Could not connect to Redis--waiting before trying again.')
        self.close(db_name)
        time.sleep(self.CONNECT_RETRY_WAIT_TIME)
        self.connect(db_name, True)
