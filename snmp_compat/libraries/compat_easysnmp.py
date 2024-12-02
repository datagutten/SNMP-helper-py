import easysnmp
from easysnmp import SNMPVariable as EasySNMPVariable

from snmp_compat import SNMPCompat, snmp_exceptions
from .easysnmp_common import EasySNMPResponse


def convert_variable(var: EasySNMPVariable):
    return EasySNMPResponse(oid=var.oid, oid_index=var.oid_index, value=var.value, snmp_type=var.snmp_type)


class EasySNMPCompat(SNMPCompat):
    def __init__(self, hostname: str, community: str, version=2, timeout=0.5, retries=1):
        super().__init__(hostname, community)
        try:
            self.session = easysnmp.Session(hostname, version, community, timeout, retries, abort_on_nonexistent=True)
        except easysnmp.EasySNMPConnectionError as e:
            raise snmp_exceptions.SNMPConnectionError(e, self)
        except SystemError as e:
            raise snmp_exceptions.SNMPError(e, self)

    def _convert_exception(self, e: easysnmp.EasySNMPError, oid: str):
        if type(e) is easysnmp.EasySNMPTimeoutError:
            raise snmp_exceptions.SNMPTimeout(e, self, oid)
        elif type(e) is easysnmp.EasySNMPConnectionError:
            raise snmp_exceptions.SNMPConnectionError(e, self, oid)
        elif type(e) in [easysnmp.EasySNMPNoSuchInstanceError, easysnmp.EasySNMPNoSuchObjectError]:
            raise snmp_exceptions.SNMPNoData(e, self, oid)
        else:
            raise snmp_exceptions.SNMPError(e, self, oid)

    def get(self, oid):
        try:
            return convert_variable(self.session.get(oid))
        except easysnmp.exceptions.EasySNMPError as e:
            self._convert_exception(e, oid)
        except SystemError as e:
            raise snmp_exceptions.SNMPError(e, self, oid)

    def get_next(self, oid):
        try:
            return convert_variable(self.session.get_next(oid))
        except easysnmp.exceptions.EasySNMPError as e:
            self._convert_exception(e, oid)
        except SystemError as e:
            raise snmp_exceptions.SNMPError(e, self, oid)

    def walk(self, oid):
        try:
            return list(map(lambda var: convert_variable(var), self.session.walk(oid)))
        except easysnmp.exceptions.EasySNMPError as e:
            self._convert_exception(e, oid)
        except SystemError as e:
            raise snmp_exceptions.SNMPError(e, self, oid)
