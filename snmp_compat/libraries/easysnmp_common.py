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
            for char in self.value:
                if not char.isprintable():
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
