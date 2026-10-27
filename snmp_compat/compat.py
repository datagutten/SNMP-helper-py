import os
from abc import ABC
from typing import Type, List

from .response import SNMPResponse

auth_levels = ['noAuthNoPriv', 'authNoPriv', 'authPriv']


class SNMPBase(ABC):
    session = None

    def close(self):
        pass

    def get(self, oid: str) -> SNMPResponse:
        raise NotImplementedError

    def get_next(self, oid: str) -> SNMPResponse:
        raise NotImplementedError

    def walk(self, oid: str) -> List[SNMPResponse]:
        raise NotImplementedError

    def bulkwalk(self, oid: str) -> List[SNMPResponse]:
        return self.walk(oid)


class SNMPCompat(SNMPBase):
    hostname: str = None
    community: str = None

    @classmethod
    def connect_v1(cls, hostname: str, community: str, timeout=0.5, retries=1):
        raise NotImplementedError

    @classmethod
    def connect_v3(cls, hostname: str, auth_username: str, auth_passphrase: str,
                   auth_protocol: str = 'MD5', context: str = None,
                   timeout: float = 0.5, retries: int = 1):
        raise NotImplementedError


def select(library=None) -> Type[SNMPCompat]:
    if library is None:
        if 'SNMP_LIBRARY' not in os.environ:
            raise AttributeError('library argument not set and SNMP_LIBRARY environment variable not set')
        else:
            library = os.environ['SNMP_LIBRARY']
    if library == 'easysnmp':
        from .libraries.compat_easysnmp import EasySNMPCompat
        return EasySNMPCompat
    elif library == 'netsnmp':
        from .libraries.compat_netsnmp import NetSNMPCompat
        return NetSNMPCompat
    elif library == 'ezsnmp':  # Try both v1 and v2
        try:
            from .libraries.compat_ezsnmp import EZSNMPCompat
            return EZSNMPCompat
        except AttributeError:
            from .libraries.compat_ezsnmp2 import EZSNMP2Compat
            return EZSNMP2Compat
    elif library == 'ezsnmp2':  # Force v2
        from .libraries.compat_ezsnmp2 import EZSNMP2Compat
        return EZSNMP2Compat
    elif library == 'pysnmp':
        from .libraries.compat_pysnmp import PySNMPCompat
        return PySNMPCompat
    else:
        raise AttributeError('Invalid library %s' % library)
