import datetime
import re

# This regular expression is used to extract the index from an OID
OID_INDEX_RE = re.compile(
    r'''(
            \.?\d+(?:\.\d+)*              # numeric OID
            |                             # or
            (?:\w+(?:[-:]*\w+)+)          # regular OID
            |                             # or
            (?:\.?iso(?:\.\w+[-:]*\w+)+)  # fully qualified OID
        )
        \.?(.*)                           # OID index
     ''',
    re.VERBOSE
)


def mac_string(mac_address):
    string = ''
    if len(mac_address) == 12:  # No conversion required
        return mac_address

    for octet in mac_address:
        octet = ord(octet)
        if octet <= 0x0f:
            string += '0'
        # Format as lower case hex digit without prefix
        string += format(octet, 'x')
    return string


def timeticks(ticks: int) -> datetime.timedelta:
    return datetime.timedelta(seconds=ticks / 100)


def normalize_oid(oid, oid_index=None):
    """
    Ensures that the index is set correctly given an OID definition.

    :param oid: the OID to normalize
    :param oid_index: the OID index to normalize
    From easysnmp/helpers.py
    """

    # Determine the OID index from the OID if not specified
    if oid_index is None and oid is not None:
        # We attempt to extract the index from an OID (e.g. sysDescr.0
        # or .iso.org.dod.internet.mgmt.mib-2.system.sysContact.0)
        match = OID_INDEX_RE.match(oid)
        if match:
            oid, oid_index = match.group(1, 2)

    return oid, oid_index


class SNMPResponse(object):
    """
    An SNMP variable binding which is used to represent a piece of
    information being retreived via SNMP.

    :param oid: the OID being manipulated
    :param oid_index: the index of the OID
    :param value: the OID value
    :param snmp_type: the snmp_type of data contained in val (please see
                      http://www.net-snmp.org/wiki/index.php/TUT:snmpset#Data_Types
                      for further information); in the case that an object
                      or instance is not found, the type will be set to
                      NOSUCHOBJECT and NOSUCHINSTANCE respectively
    """

    def __init__(self, oid=None, oid_index=None, value=None, snmp_type=None):
        self.oid, self.oid_index = normalize_oid(oid, oid_index)
        self.oid = self.oid.replace('iso.', '.1.')
        self.value = value
        self.snmp_type = snmp_type

    def __repr__(self):
        return (
            "<{0} value={1} (oid={2}, oid_index={3}, snmp_type={4})>".format(
                self.__class__.__name__,
                self.value, self.oid,
                self.oid_index, self.snmp_type
            )
        )

    def hex_string(self):
        string = ''
        for octet in self.value:
            octet = ord(octet)
            if octet <= 0x0f:
                string += '0'
            # Format as lower case hex digit without prefix
            string += format(octet, 'x')
        return string

    def typed_value(self):
        raise NotImplementedError
