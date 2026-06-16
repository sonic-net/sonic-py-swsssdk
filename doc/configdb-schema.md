Schema data is defined in ABNF [RFC5234](https://tools.ietf.org/html/rfc5234) syntax.

### Definitions of common tokens
    name                    = 1*DIGIT/1*ALPHA
    ref_hash_key_reference  = "[" hash_key "]" ; The token is a refernce to another valid DB key.
    hash_key                = name             ; a valid key name (i.e. exists in DB)
    LIST(type)              = *(type,)type     ; a list of values in specific type, seperated by ','
    IPprefix       = IPv4prefix / IPv6prefix   ; an instance of this key/value pair will be repeated for each prefix
    IPv6prefix     =                             6( h16 ":" ) ls32
                    /                       "::" 5( h16 ":" ) ls32
                    / [               h16 ] "::" 4( h16 ":" ) ls32
                    / [ *1( h16 ":" ) h16 ] "::" 3( h16 ":" ) ls32
                    / [ *2( h16 ":" ) h16 ] "::" 2( h16 ":" ) ls32
                    / [ *3( h16 ":" ) h16 ] "::"    h16 ":"   ls32
                    / [ *4( h16 ":" ) h16 ] "::"              ls32
                    / [ *5( h16 ":" ) h16 ] "::"              h16
                    / [ *6( h16 ":" ) h16 ] "::"
     h16           = 1*4HEXDIG
     ls32          = ( h16 ":" h16 ) / IPv4address
     IPv4prefix    = dec-octet "." dec-octet "." dec-octet "." dec-octet "/" %d1-32

### DEVICE_METADATA table

    ; Key
    device_metadata_key = 'localhost'    ; there shall be only one instance of DEVICE_METADATA table, and the key shall always be 'localhost'
    ; Attributes
    deployment_id       = 1*2DIGIT       ; an integer between 0 and 99 to indicate the deployment enviroment of device
    bgp_asn             = 1*5DIGIT       ; local as number. it is based on the fact that currently only single instance of BGP is supported on SONiC. If multiple instances are to be supported this field will needs to be extended into another table.
    hostname            = 1*64VCHAR      
    hwsku               = 1*64VCHAR
    type                = 1*64VCHAR      ; deployment type of the switch. Apps might enable/disable some features based on value of this field.    
    
    Example:
    127.0.0.1:6379[4]> hgetall DEVICE_METADATA:localhost
    1) "bgp_asn"
    2) "65000"
    3) "hwsku"
    4) "MSN2700"
    5) "hostname"
    6) "switch1"
    7) "type"
    8) "ToRRouter"
    
### BGP_NEIGHBOR table

    ; Stores BGP session information
    ; Key
    bgp_neighbor_key    = IPAddress      ; IP address of BGP neighbor
    ; Attributes
    asn                 = 1*5DIGIT       ; remote ASN
    admin_status        = "down" / "up"  ; admin status
    name                = 1*64VCHAR      ; neighbor host name
    peer_addr           = IPPrefix       ; local address used to peer with neighbor

    Example:
    127.0.0.1:6379[4]> keys BGP_NEIGHBOR:*
     1) "BGP_NEIGHBOR:10.0.0.31"
     2) "BGP_NEIGHBOR:10.0.0.39"
     3) "BGP_NEIGHBOR:10.0.0.11"
     4) "BGP_NEIGHBOR:10.0.0.7"
     5) "BGP_NEIGHBOR:10.0.0.15"
     6) "BGP_NEIGHBOR:10.0.0.45"
     7) "BGP_NEIGHBOR:10.0.0.35"
     8) "BGP_NEIGHBOR:10.0.0.51"
     9) "BGP_NEIGHBOR:10.0.0.1"
    10) "BGP_NEIGHBOR:10.0.0.43"
    11) "BGP_NEIGHBOR:10.0.0.3"
    12) "BGP_NEIGHBOR:10.0.0.21"
    13) "BGP_NEIGHBOR:10.0.0.55"
    14) "BGP_NEIGHBOR:10.0.0.17"
    15) "BGP_NEIGHBOR:10.0.0.19"
    16) "BGP_NEIGHBOR:10.0.0.25"
    17) "BGP_NEIGHBOR:10.0.0.63"
    18) "BGP_NEIGHBOR:10.0.0.41"
    19) "BGP_NEIGHBOR:10.0.0.29"
    20) "BGP_NEIGHBOR:10.0.0.33"
    21) "BGP_NEIGHBOR:10.0.0.5"
    22) "BGP_NEIGHBOR:10.0.0.23"
    23) "BGP_NEIGHBOR:10.0.0.13"
    24) "BGP_NEIGHBOR:10.0.0.27"
    25) "BGP_NEIGHBOR:10.0.0.57"
    26) "BGP_NEIGHBOR:10.0.0.47"
    27) "BGP_NEIGHBOR:10.0.0.37"
    28) "BGP_NEIGHBOR:10.0.0.53"
    29) "BGP_NEIGHBOR:10.0.0.49"
    30) "BGP_NEIGHBOR:10.0.0.9"
    31) "BGP_NEIGHBOR:10.0.0.61"
    32) "BGP_NEIGHBOR:10.0.0.59"
    127.0.0.1:6379[4]> hgetall BGP_NEIGHBOR:10.0.0.13
    1) "admin_status"
    2) "up"
    3) "peer_addr"
    4) "10.0.0.12"
    5) "asn"
    6) "65200"
    7) "name"
    8) "ARISTA07T2"

### BGP_PEER_RANGE table

    ; Key
    bgp_peer_range_key    = 1*64VCHAR
    ; Attributes
    name                  = 1*64VCHAR
    ip_range              = LIST(IPPrefix)


### MGMT_INTERFACE table

    ; Key
    port_name             = 1*64VCHAR            ; name of mgmt port that the ip interface attach to
    ip_prefix             = IPPrefix    
    ; Attributes
    gwaddr                = IPAddress  
    forced_mgmt_routes    = LIST(IPPrefix)       ; the prefixes to which route will be force to be going through mgmt port
    

### LOOPBACK_INTERFACE table

    ; Key
    port_name              = 1*64VCHAR
    ip_prefix              = IPPrefix
    ; Attributes
    ; No attributes
    

### PORT table

    ; Key
    name                  = 1*64VCHAR
    ; Attributes
    alias                 = 1*64VCHAR
    MTU                   = 1*5DIGIT  
    front_panel_index     = 1*3DIGIT
    speed                 = 1*5DIGIT  
    
### INTERFACE table

    ; Key
    port_name              = 1*64VCHAR
    ip_prefix              = IPPrefix
    ; Attributes
    ; No attributes
    
### PORTCHANNEL table

    ; Key
    name                  = 1*64VCHAR
    ; Attributes
    members               = LIST(1*64VCHAR)
    
### PORTCHANNEL_INTERFACE table

    ; Key
    portchannel_name      = 1*64VCHAR
    ip_prefix             = IPPrefix
    ; Attributes
    ; No attributes

### VLAN table

    ; Key
    name                 = 1*64VCHAR
    ; Attributes
    id                   = 1*5DIGIT 
    members              = LIST(1*64VCHAR)
    
### VLAN_INTERFACE table

    ; Key
    vlan_name             = 1*64VCHAR
    ip_prefix             = IPPrefix
    ; Attributes
    ; No attributes

### DEVICE_NEIGHBOR table

    ; Key
    neighbor_name         = 1*64VCHAR    ; neighbor host name
    ; Attributes
    port                  = 1*64VCHAR
    local_port            = 1*64VCHAR
    type                  = 1*64VCHAR
    hwsku                 = 1*64VCHAR
    mgmt_addr             = IPPrefix
    lo_addr               = IPPrefix

### MIRROR_SESSION table

    ; Key
    mirror_session_key    = 1*64VCHAR
    ; Attributes
    src_ip                = IPPrefix
    dst_ip                = IPPrefix
      
### ACL_TABLE table

    ; Key
    acl_table_key        = 1*64VCHAR
    ; Attributes
    policy_desc   = 1*255VCHAR              ; name of the ACL policy table description
    type          = "mirror"/"l3"           ; type of acl table, every type of
                                            ; table defines the match/action a
                                            ; specific set of match and actions.
    ports         = [0-max_ports]*port_name ; the ports to which this ACL
                                            ; table is applied, can be emtry
                                            ; value annotations
      
### NTP_SERVER table

    ; Key
    server_url           =  1*128VCHAR
    ; No attributes
    
### SYSLOG_SERVER table

    ; Key
    server_url           =  1*128VCHAR
    ; No attributes

### DHCP_SERVER table

    ; Key
    server_url           =  1*128VCHAR
    ; No attributes
    
