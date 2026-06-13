import datetime
from typing import Literal

import ezsnmp

from snmp_compat import SNMPCompat, SNMPResponse, snmp_exceptions


def convert_response(response: ezsnmp.Result) -> SNMPResponse:
    oid = f"{response.oid.replace('iso.', '.1.')}.{response.index}"
    if response.type == 'NOSUCHINSTANCE':
        raise snmp_exceptions.SNMPNoData(oid=oid)
    return EzSNMPResponse(oid, response.index, response.converted_value, response.type)


class EzSNMPResponse(SNMPResponse):
    def typed_value(self):
        if self.snmp_type == '""':
            return ''

        elif self.snmp_type == 'Hex-STRING':
            return self.hex_string()
        elif self.snmp_type == 'Timeticks':
            return datetime.timedelta(seconds=int(self.value) / 100)
        else:
            return self.value


class EZSNMP2Compat(SNMPCompat):
    def __init__(self, hostname, community, version: Literal[1, 2, 3] = 2, timeout=1, retries=1):
        super().__init__(hostname, community)
        try:
            self.session = ezsnmp.Session(hostname=hostname, version=version, community=community, timeout=timeout,
                                          retries=retries)
        except ezsnmp.exceptions.GenericError as e:
            raise snmp_exceptions.SNMPConnectionError(e, self)

    def _convert_exception(self, e: ezsnmp.exceptions.GenericError, oid: str):
        oid = oid.replace('iso.', '.1.')
        if type(e) is ezsnmp.exceptions.TimeoutError:
            raise snmp_exceptions.SNMPTimeout(e, self, oid)
        # It seems like ezsnmp v2 returns NOSUCHINSTANCE as response type instead of throwing an exception, but the exception is defined, so we handle it
        elif type(e) in [ezsnmp.exceptions.NoSuchInstanceError, ezsnmp.exceptions.NoSuchObjectError,
                         ezsnmp.exceptions.NoSuchNameError]:
            raise snmp_exceptions.SNMPNoData(e, self, oid)
        else:
            raise snmp_exceptions.SNMPError(e, self, oid)

    def get(self, oid):
        try:
            response = self.session.get(oid)
            return convert_response(response[0])
        except ezsnmp.exceptions.GenericError as e:
            self._convert_exception(e, oid)

    def get_next(self, oid):
        try:
            response = self.session.get_next(oid)
            return convert_response(response[0])
        except ezsnmp.exceptions.GenericError as e:
            self._convert_exception(e, oid)

    def walk(self, oid):
        try:
            return list(map(lambda var: convert_response(var), self.session.walk(oid)))
        except ezsnmp.exceptions.GenericError as e:
            self._convert_exception(e, oid)
        except SystemError as e:
            raise snmp_exceptions.SNMPError(e, self, oid)

    def bulkwalk(self, oid):
        if self.session.version < 2:
            return self.walk(oid)

        try:
            return list(map(lambda var: convert_response(var), self.session.bulkwalk(oid)))
        except ezsnmp.exceptions.GenericError as e:
            self._convert_exception(e, oid)
        except SystemError as e:
            raise snmp_exceptions.SNMPError(e, self, oid)
