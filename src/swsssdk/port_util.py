"""
Bridge/Port mapping utility library.
"""
import swsssdk
import re


SONIC_ETHERNET_RE_PATTERN = "^Ethernet(\d+)$"
"""
Ethernet-BP refers to BackPlane interfaces
in multi-asic platform.
"""
SONIC_ETHERNET_BP_RE_PATTERN = "^Ethernet-BP(\d+)$"
SONIC_VLAN_RE_PATTERN = "^Vlan(\d+)$"
SONIC_PORTCHANNEL_RE_PATTERN = "^PortChannel(\d+)$"
SONIC_MGMT_PORT_RE_PATTERN = "^eth(\d+)$"


class BaseIdx:
    ethernet_base_idx = 1
    vlan_interface_base_idx = 2000
    ethernet_bp_base_idx = 9000
    portchannel_base_idx = 1000
    mgmt_port_base_idx = 10000

def get_index(if_name):
    """
    OIDs are 1-based, interfaces are 0-based, return the 1-based index
    Ethernet N = N + 1
    Vlan N = N + 2000
    Ethernet_BP N = N + 9000
    PortChannel N = N + 1000
    eth N = N + 10000
    """
    return get_index_from_str(if_name.decode())


def get_index_from_str(if_name):
    """
    OIDs are 1-based, interfaces are 0-based, return the 1-based index
    Ethernet N = N + 1
    Vlan N = N + 2000
    Ethernet_BP N = N + 9000
    PortChannel N = N + 1000
    eth N = N + 10000
    """
    patterns = {
        SONIC_ETHERNET_RE_PATTERN: BaseIdx.ethernet_base_idx,
        SONIC_ETHERNET_BP_RE_PATTERN: BaseIdx.ethernet_bp_base_idx,
        SONIC_VLAN_RE_PATTERN: BaseIdx.vlan_interface_base_idx,
        SONIC_PORTCHANNEL_RE_PATTERN: BaseIdx.portchannel_base_idx,
        SONIC_MGMT_PORT_RE_PATTERN: BaseIdx.mgmt_port_base_idx
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
    if_lag_name_map = db.get_all('COUNTERS_DB', 'COUNTERS_LAG_NAME_MAP', blocking=True)
    if_name_map.update(if_lag_name_map)

    oid_pfx = len("oid:0x")
    if_name_map = {if_name: sai_oid[oid_pfx:] for if_name, sai_oid in if_name_map.items()}

    if_id_map = {sai_oid: if_name for if_name, sai_oid in if_name_map.items()
                 # only map the interface if it's a style understood to be a SONiC interface.
                 if get_index(if_name) is not None}

    return if_name_map, if_id_map

def get_bridge_port_map(db):
    """
        Get the Bridge port mapping from ASIC DB
    """
    db.connect('ASIC_DB')
    br_port_str = db.keys('ASIC_DB', "ASIC_STATE:SAI_OBJECT_TYPE_BRIDGE_PORT:*")
    if not br_port_str:
        return {}

    if_br_oid_map = {}
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

def get_vlan_id_from_bvid(db, bvid):
    """
        Get the Vlan Id from Bridge Vlan Object
    """
    db.connect('ASIC_DB')
    vlan_obj = db.keys('ASIC_DB', "ASIC_STATE:SAI_OBJECT_TYPE_VLAN:" + bvid)
    vlan_entry = db.get_all('ASIC_DB', vlan_obj[0], blocking=True)
    vlan_id = vlan_entry[b"SAI_VLAN_ATTR_VLAN_ID"]

    return vlan_id

def get_rif_port_map(db):
    """
        Get the RIF port mapping from ASIC DB
    """
    db.connect('ASIC_DB')
    rif_keys_str = db.keys('ASIC_DB', "ASIC_STATE:SAI_OBJECT_TYPE_ROUTER_INTERFACE:*")
    if not rif_keys_str:
        return {}

    rif_port_oid_map = {}
    for rif_s in rif_keys_str:
        rif_id = rif_s.lstrip(b"ASIC_STATE:SAI_OBJECT_TYPE_ROUTER_INTERFACE:oid:0x")
        ent = db.get_all('ASIC_DB', rif_s, blocking=True)
        if b"SAI_ROUTER_INTERFACE_ATTR_PORT_ID" in ent:
            port_id = ent[b"SAI_ROUTER_INTERFACE_ATTR_PORT_ID"].lstrip(b"oid:0x")
            rif_port_oid_map[rif_id] = port_id

    return rif_port_oid_map

def get_vlan_interface_oid_map(db):
    """
        Get Vlan Interface names and sai oids
    """
    db.connect('COUNTERS_DB')
    rif_name_map = db.get_all('COUNTERS_DB', 'COUNTERS_RIF_NAME_MAP', blocking=True)
    rif_type_name_map = db.get_all('COUNTERS_DB', 'COUNTERS_RIF_TYPE_MAP', blocking=True)

    if not rif_name_map or not rif_type_name_map:
        return {}

    oid_pfx = len("oid:0x")
    vlan_if_name_map = {}

    for if_name, sai_oid in rif_name_map.items():
        # Check if RIF is l3 vlan interface
        if rif_type_name_map[sai_oid] == b'SAI_ROUTER_INTERFACE_TYPE_VLAN':
            # Check if interface name is in style understood to be a SONiC interface
            if get_index(if_name):
                vlan_if_name_map[sai_oid[oid_pfx:]] = if_name

    return vlan_if_name_map
