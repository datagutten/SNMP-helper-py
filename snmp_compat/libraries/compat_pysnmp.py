import asyncio
import datetime
from typing import List, Any

import pysnmp.hlapi.v3arch.asyncio as v3arch
from pysnmp.entity.engine import SnmpEngine
from pysnmp.error import PySnmpError
from pysnmp.hlapi.v3arch.asyncio import UsmUserData, ContextData, CommunityData
from pysnmp.proto import rfc1902
from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

from snmp_compat import SNMPCompat, SNMPResponse, snmp_exceptions


class PYSNMPResponse(SNMPResponse):
    value: Any
    _response = None

    def __init__(self, oid=None, oid_index=None, response=None, snmp_type=None):
        if not hasattr(response, '_value'):
            value = None
        else:
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

    def ip_address(self):
        string = ''
        for octet in self._response.asOctets():
            if octet > 255:
                raise ValueError("Invalid IP address")
            string += '%d.' % octet
        return string[:-1]

    def typed_value(self):
        if self.snmp_type == rfc1902.TimeTicks:
            return datetime.timedelta(seconds=int(self._response) / 100)
        elif self.snmp_type == rfc1902.OctetString:  # OctetString:
            string_value = str(self._response)
            if self.value == b'':
                return ''
            for char in string_value:
                if not char.isprintable() and not char.isspace():
                    return self.hex_string()
            return string_value
        elif self.snmp_type == rfc1902.IpAddress:
            return self.ip_address()
        elif hasattr(self.snmp_type, 'typeId') and self.snmp_type.typeId == 4:
            return self.value.decode(self.snmp_type.encoding)
        else:
            return self.value


class PySNMPCompat(SNMPCompat):
    _transport: v3arch.UdpTransportTarget = None
    _auth_data: CommunityData | UsmUserData
    _context_data: ContextData

    def __init__(self, hostname: str, auth_data: CommunityData | UsmUserData, context_data: ContextData):
        self.hostname = hostname
        self._auth_data = auth_data
        self._context_data = context_data
        asyncio.run(self._async_connect())

    @classmethod
    def connect_v1(cls, hostname: str, community: str, version=1, timeout=0.5, retries=1):
        assert version <= 2
        version = version - 1  # 0 = SNMPv1, 1= SNMPv2c
        auth_data = CommunityData(community, mpModel=version)
        return cls(hostname, auth_data, ContextData())

    @classmethod
    def connect_v3(cls, hostname: str, auth_username: str, auth_passphrase: str,
                   auth_protocol: str = None, context: str = None,
                   timeout: float = 0.5, retries: int = 1):
        auth_data = UsmUserData(auth_username, auth_passphrase, authProtocol=auth_protocol)
        context_data = ContextData(contextName=context)
        return cls(hostname, auth_data, context_data)

    @property
    def community(self):
        if type(self._auth_data) is CommunityData:
            return self._auth_data.communityName
        else:
            return self._auth_data.userName

    def _convert_response(self, response, oid: str = None):
        error_indication, error_status, error_index, var_binds = response
        if var_binds:
            oid = '.' + str(var_binds[0][0])

        if error_status and str(error_status) == 'noSuchName':
            raise snmp_exceptions.SNMPNoData(oid=oid, session=self)
        if error_indication is not None:
            if str(error_indication) == 'No SNMP response received before timeout':
                raise snmp_exceptions.SNMPTimeout(oid=oid, session=self)
            else:
                raise snmp_exceptions.SNMPError(str(error_indication))

        identity, response = var_binds[0]
        return PYSNMPResponse(oid=oid, response=response, snmp_type=type(response))

    async def _async_connect(self):
        try:
            self._transport = await v3arch.UdpTransportTarget.create((self.hostname, 161))
        except PySnmpError as e:
            raise snmp_exceptions.SNMPConnectionError(e, self)

    async def get_async(self, oid: str):
        obj = ObjectType(ObjectIdentity(oid))
        response = await v3arch.get_cmd(SnmpEngine(),
                                        self._auth_data, self._transport, self._context_data, obj)
        return self._convert_response(response, oid)

    async def get_next_async(self, oid: str):
        obj = ObjectType(ObjectIdentity(oid))
        response = await v3arch.next_cmd(SnmpEngine(),
                                         self._auth_data, self._transport, self._context_data, obj)
        return self._convert_response(response, oid)

    async def walk_async(self, oid: str) -> List[SNMPResponse]:
        obj = ObjectType(ObjectIdentity(oid))
        response = v3arch.walk_cmd(SnmpEngine(),
                                   self._auth_data, self._transport, self._context_data, obj)
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
