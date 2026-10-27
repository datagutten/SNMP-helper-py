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
    def __init__(self, session):
        self.session = session
        #
        # except ezsnmp.exceptions.GenericError as e:
        #     raise snmp_exceptions.SNMPConnectionError(e, self)

    @classmethod
    def connect_v1(cls, hostname: str, community: str, timeout=0.5, retries=1, version: Literal[1, 2] = 2):
        session = ezsnmp.Session(hostname=hostname, version=version, community=community,
                                 timeout=timeout,
                                 retries=retries)
        return cls(session)

    @classmethod
    def connect_v3(cls, hostname: str, auth_username: str, auth_passphrase: str,
                   auth_protocol: str = 'MD5', context: str = None,
                   timeout: float = 0.5, retries: int = 1):

        security_level = 'authNoPriv'

        session = ezsnmp.Session(hostname=hostname, context=context, version=3,
                                 auth_protocol=auth_protocol,
                                 security_username=auth_username,
                                 auth_passphrase=auth_passphrase, timeout=timeout,
                                 retries=retries, security_level=security_level)
        return cls(session)

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
