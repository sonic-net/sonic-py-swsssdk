# Python SwSS SDK
Python utility library for SONiC Switch State Service database access

See the [SONiC Website](http://azure.github.io/SONiC/) for more information about the SONiC project

Database names are defined by Switch State Service. See the [sonic-swss-common](https://github.com/Azure/sonic-swss-common/blob/master/common/schema.h) project.

### Example Usage
```python
>>> import swsssdk
>>> swss = swsssdk.SonicV2Connector()
>>> swss.db_list
dict_keys(['COUNTERS_DB', 'ASIC_DB', 'APPL_DB'])
>>> dir(swss)
['APPL_DB', 'ASIC_DB', 'CONNECT_RETRY_WAIT_TIME', 'COUNTERS_DB', 'DATA_RETRIEVAL_WAIT_TIME', 'KEYSPACE_EVENTS', 'KEYSPACE_PATTERN', 'PUB_SUB_MAXIMUM_DATA_WAIT', 'PUB_SUB_NOTIFICATION_TIMEOUT', 'REDIS_HOST', 'REDIS_PORT', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_connection_error_handler', '_onetime_connect', '_persistent_connect', '_subscribe_keyspace_notification', '_unavailable_data_handler', 'close', 'connect', 'db_list', 'db_map', 'get', 'get_all', 'get_dbid', 'get_redis_client', 'keys', 'keyspace_notification_channels', 'redis_clients', 'set']
>>> swss.connect(swss.APPL_DB)
>>> swss.keys(swss.APPL_DB)
[b'PORT_TABLE:Ethernet8', b'INTF_TABLE:Ethernet16:10.0.0.8/31', b'LLDP_ENTRY_TABLE:Ethernet4', b'PORT_TABLE:Ethernet76', b'PORT_TABLE_VALUE_QUEUE', b'NEIGH_TABLE:eth0:10.3.147.40', ...]
```
