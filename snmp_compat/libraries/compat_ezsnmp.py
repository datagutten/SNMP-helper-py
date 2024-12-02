from typing import Literal

import ezsnmp

from snmp_compat import SNMPCompat, SNMPResponse, snmp_exceptions
from .easysnmp_common import EasySNMPResponse


def convert_response(response: ezsnmp.SNMPVariable) -> SNMPResponse:
    return EasySNMPResponse(response.oid, response.oid_index, response.value, response.snmp_type)


class EZSNMPCompat(SNMPCompat):
    def __init__(self, hostname, community, version: Literal[1, 2, 3] = 2, timeout=1, retries=1):
        super().__init__(hostname, community)
        try:
            self.session = ezsnmp.Session(hostname, version, community, timeout, retries, abort_on_nonexistent=True)
        except ezsnmp.exceptions.EzSNMPConnectionError as e:
            raise snmp_exceptions.SNMPConnectionError(e, self)

    def _convert_exception(self, e: ezsnmp.EzSNMPError, oid: str):
        oid = oid.replace('iso.', '.1.')
        if type(e) is ezsnmp.EzSNMPTimeoutError:
            raise snmp_exceptions.SNMPTimeout(e, self, oid)
        elif type(e) in [ezsnmp.EzSNMPNoSuchInstanceError, ezsnmp.EzSNMPNoSuchObjectError]:
            raise snmp_exceptions.SNMPNoData(e, self, oid)
        else:
            raise snmp_exceptions.SNMPError(e, self, oid)

    def get(self, oid):
        try:
            response = self.session.get(oid)
            return convert_response(response)
        except ezsnmp.exceptions.EzSNMPError as e:
            self._convert_exception(e, oid)

    def get_next(self, oid):
        try:
            response = self.session.get_next(oid)
            return convert_response(response)
        except ezsnmp.exceptions.EzSNMPError as e:
            self._convert_exception(e, oid)

    def walk(self, oid):
        try:
            return list(map(lambda var: convert_response(var), self.session.walk(oid)))
        except ezsnmp.exceptions.EzSNMPError as e:
            self._convert_exception(e, oid)
        except SystemError as e:
            raise snmp_exceptions.SNMPError(e, self, oid)
