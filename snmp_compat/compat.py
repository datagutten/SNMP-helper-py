import os
from abc import ABC
from typing import Type, List

from .response import SNMPResponse


class SNMPCompat(ABC):
    session = None
    hostname: str = None
    community: str = None

    def __init__(self, hostname, community, version=0, timeout=0.5, retries=1):
        self.hostname = hostname
        self.community = community

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
    elif library == 'ezsnmp':
        from .libraries.compat_ezsnmp import EZSNMPCompat
        return EZSNMPCompat
    elif library == 'pysnmp':
        from .libraries.compat_pysnmp import PySNMPCompat
        return PySNMPCompat
    else:
        raise AttributeError('Invalid library %s' % library)
