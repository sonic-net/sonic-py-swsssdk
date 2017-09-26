"""
Bridge/Port mapping utility library.
"""
import swsssdk
import re

SONIC_ETHERNET_RE_PATTERN = "^Ethernet(\d+)$"
SONIC_PORTCHANNEL_RE_PATTERN = "^PortChannel(\d+)$"

def get_index(if_name):
    """
    OIDs are 1-based, interfaces are 0-based, return the 1-based index
    Ethernet N = N + 1
    PortChannel N = N + 1000
    """
    return get_index_from_str(if_name.decode())


def get_index_from_str(if_name):
    """
    OIDs are 1-based, interfaces are 0-based, return the 1-based index
    Ethernet N = N + 1
    PortChannel N = N + 1000
    """
    patterns = {
        SONIC_ETHERNET_RE_PATTERN: 1,
        SONIC_PORTCHANNEL_RE_PATTERN: 1000
    }

    for pattern, baseidx in patterns.items():
        match = re.match(pattern, if_name)
        if match:
            return int(match.group(1)) + baseidx

def get_interface_oid_map(db):
    """
        Get the Interface names from Counters DB
    """
    db.connect('COUNTERS_DB')
    if_name_map = db.get_all('COUNTERS_DB', 'COUNTERS_PORT_NAME_MAP', blocking=True)
    if_id_map = {sai_oid: if_name for if_name, sai_oid in if_name_map.items()
                 # only map the interface if it's a style understood to be a SONiC interface.
                 if get_index(if_name) is not None}

    return if_name_map, if_id_map

def get_bridge_port_map(db):
    """
        Get the Bridge port mapping from ASIC DB
    """
    db.connect('ASIC_DB')
    if_br_oid_map = {}
    br_port_str = db.keys('ASIC_DB', "ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT:*")
    if not br_port_str:
        return

    offset = len("ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT:")
    oid_pfx = len("oid:0x")
    for br_s in br_port_str:
        # Example output: ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT:oid:0x3a000000000616
        br_port_id = br_s[(offset + oid_pfx):]
        ent = db.get_all('ASIC_DB', br_s, blocking=True)
        if b"SAI_BRIDGE_PORT_ATTR_PORT_ID" in ent:
            port_id = ent[b"SAI_BRIDGE_PORT_ATTR_PORT_ID"][oid_pfx:]
            if_br_oid_map[br_port_id] = port_id

    return if_br_oid_map

