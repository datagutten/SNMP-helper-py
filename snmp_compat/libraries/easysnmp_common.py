import datetime

from snmp_compat import SNMPCompat, SNMPResponse


class EasySNMPCommon(SNMPCompat):
    pass


class EasySNMPResponse(SNMPResponse):
    """
    Common methods for EasySNMP and its fork EzSNMP
    """

    def typed_value(self):
        if self.snmp_type == 'OCTETSTR':
            # Detect hex string, match C code in netsnmp-py3
            # https://github.com/xstaticxgpx/netsnmp-py3/blob/a8c83851351f04a304ff81dbbd1d92433a43eac4/netsnmp/interface.c#L90
            for char in self.value:
                if not char.isprintable() and not char.isspace():
                    return self.hex_string()
            return self.value
        elif self.snmp_type in ['INTEGER', 'COUNTER', 'COUNTER64', 'GAUGE']:
            return int(self.value)
        elif self.snmp_type == 'TICKS':
            return datetime.timedelta(seconds=int(self.value) / 100)
        elif self.snmp_type == 'OBJECTID':
            return self.value  # Value 'ccitt.0.0'
        else:
            return self.value
