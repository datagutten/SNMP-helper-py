import asyncio
import datetime
from typing import List

from pysnmp.error import PySnmpError
from pysnmp.hlapi.v3arch.asyncio import *

from snmp_compat import SNMPCompat, SNMPResponse, snmp_exceptions


class PYSNMPResponse(SNMPResponse):
    value: any
    _response = None

    def __init__(self, oid=None, oid_index=None, response=None, snmp_type=None):
        # noinspection PyProtectedMember
        value = response._value
        self._response = response
        super().__init__(oid, oid_index, value, snmp_type)

    def hex_string(self):
        string = ''
        for octet in self._response.asOctets():
            if octet <= 0x0f:
                string += '0'
            # Format as lower case hex digit without prefix
            string += format(octet, 'x')
        return string

    def typed_value(self):
        if type(self._response) in [Integer32, Counter32, Counter64, Gauge32]:
            return self.value
        elif self.snmp_type == TimeTicks:
            return datetime.timedelta(seconds=int(self._response) / 100)
        elif self.snmp_type == OctetString:
            string_value = str(self._response)
            if self.value == b'':
                return ''
            for char in string_value:
                if not char.isprintable():
                    return self.hex_string()
            return string_value
        else:
            return str(self._response)


class PySNMPCompat(SNMPCompat):
    _transport: UdpTransportTarget = None

    def __init__(self, hostname, community, version=0, timeout=0.5, retries=1):
        super().__init__(hostname, community)

        self.community_data = CommunityData(community, mpModel=version)  # 1= SNMPv2c
        asyncio.run(self._async_connect())

    def _convert_response(self, response, oid: str = None):
        error_indication, error_status, error_index, var_binds = response
        if var_binds:
            oid = '.' + str(var_binds[0][0])

        if error_status and str(error_status) == 'noSuchName':
            raise snmp_exceptions.SNMPNoData(oid=oid, session=self)
        if error_indication and str(error_indication) == 'No SNMP response received before timeout':
            raise snmp_exceptions.SNMPTimeout(oid=oid, session=self)

        identity, response = var_binds[0]
        return PYSNMPResponse(oid=oid, response=response, snmp_type=type(response))

    async def _async_connect(self):
        try:
            self._transport = await UdpTransportTarget.create((self.hostname, 161))
        except PySnmpError as e:
            raise snmp_exceptions.SNMPConnectionError(e, self)

    async def get_async(self, oid: str):
        obj = ObjectType(ObjectIdentity(oid))
        response = await get_cmd(SnmpEngine(),
                                 self.community_data, self._transport, ContextData(), obj)
        return self._convert_response(response, oid)

    async def get_next_async(self, oid: str):
        obj = ObjectType(ObjectIdentity(oid))
        response = await next_cmd(SnmpEngine(),
                                  self.community_data, self._transport, ContextData(), obj)
        return self._convert_response(response, oid)

    async def walk_async(self, oid: str) -> List[SNMPResponse]:
        obj = ObjectType(ObjectIdentity(oid))
        response = walk_cmd(SnmpEngine(),
                            self.community_data, self._transport, ContextData(), obj)
        entries = []
        async for entry in response:
            entry = self._convert_response(entry)
            if entry.oid.find(oid[1:]) == -1:
                break
            entries.append(entry)
        return entries

    def get(self, oid: str) -> SNMPResponse:
        return asyncio.run(self.get_async(oid))

    def get_next(self, oid: str) -> SNMPResponse:
        return asyncio.run(self.get_next_async(oid))

    def walk(self, oid: str) -> List[SNMPResponse]:
        return asyncio.run(self.walk_async(oid))
