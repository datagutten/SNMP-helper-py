import re
from datetime import timedelta

import netsnmp
# noinspection PyProtectedMember,PyUnresolvedReferences
from netsnmp._api import SNMPError

from snmp_compat import SNMPCompat, snmp_exceptions, SNMPResponse


def get_exception(message: str):
    if message.find('null response') > -1:
        return snmp_exceptions.SNMPNoData
    if message.find('Timeout') > -1:
        return snmp_exceptions.SNMPTimeout
    else:
        return snmp_exceptions.SNMPError


def convert_response(data: tuple):
    return NetSNMPResponse(oid=data[0], snmp_type=data[1], value=data[2])


class NetSNMPCompat(SNMPCompat):

    def __init__(self, hostname, community, version=0, timeout=0.5, retries=1):
        super().__init__(hostname, community)
        try:
            self.session = netsnmp.SNMPSession(peername=hostname, community=community, version=version, timeout=timeout,
                                               retries=retries)
        except (SNMPError, SystemError, RuntimeError) as e:
            # raise get_exception(str(e))(e)
            raise snmp_exceptions.SNMPConnectionError(e, self)

    def get(self, oid):
        try:
            data = self.session.get(oid)
        except (SNMPError, SystemError, TimeoutError) as e:
            raise get_exception(str(e))(e, self, oid)

        return convert_response(data[0])

    def get_next(self, oid):
        try:
            data = self.session.getnext(oid)
        except (SNMPError, SystemError, TimeoutError) as e:
            raise get_exception(str(e))(e, self, oid)

        return convert_response(data[0])

    def walk(self, oid):
        try:
            data = self.session.walk(oid)
            return list(map(lambda element: convert_response(element), data))
        except (SNMPError, SystemError) as e:
            raise get_exception(str(e))(e, self, oid)


class NetSNMPResponse(SNMPResponse):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.snmp_type == 'NULL':
            raise snmp_exceptions.SNMPNoData(oid=self.oid)

    def typed_value(self):
        if self.snmp_type == 'STRING':
            return self.value.replace('"', '')
        elif self.snmp_type in ['INTEGER', 'Gauge32', 'Counter32']:
            return int(self.value)
        elif self.snmp_type == 'Timeticks':
            matches = re.findall(r'[0-9]+', self.value)
            return timedelta(days=int(matches[0]), hours=int(matches[1]), minutes=int(matches[2]),
                             seconds=int(matches[3]), milliseconds=int(matches[4]))
        elif self.snmp_type == 'Hex-STRING':
            matches = re.findall(r'([A-F0-9]{2})\s', self.value)
            value = ''
            for byte in matches:
                octet = int(byte, 16)
                if octet <= 0x0f:
                    value += '0'
                value += format(octet, 'x')
            return value
        elif self.snmp_type == 'NULL':
            raise snmp_exceptions.SNMPNoData(oid=self.oid)
        else:
            return self.value

    def hex_string(self):
        if self.snmp_type == 'Hex-STRING':
            return self.typed_value()
        else:
            return super().hex_string()
