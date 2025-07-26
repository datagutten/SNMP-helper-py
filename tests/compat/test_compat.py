import datetime
import os
import unittest

from snmp_compat import snmp_exceptions
from snmp_compat.compat import select

SNMPSession = select(os.getenv('SNMP_LIBRARY'))

print('Running tests with SNMP library %s' % os.getenv('SNMP_LIBRARY'))

snmpsim_host = os.getenv('SNMPSIM_HOST')


class SNMPTestCase(unittest.TestCase):

    def test_invalid_oid(self):
        session = SNMPSession(snmpsim_host, 'public')
        with self.assertRaises(snmp_exceptions.SNMPNoData) as context:
            session.get('.1.7.7.7.7')
        self.assertEqual('No data for oid .1.7.7.7.7',
                         str(context.exception))

    def test_connection_error(self):
        with self.assertRaises(snmp_exceptions.SNMPConnectionError) as context:
            SNMPSession('127.0.0.1.2', 'ciscobad')
        self.assertIn('Unable to connect to 127.0.0.1.2 with community ciscobad',
                      str(context.exception))

    def test_timeout(self):
        with self.assertRaises(snmp_exceptions.SNMPTimeout) as context:
            session = SNMPSession(snmpsim_host, 'ciscobad')
            session.get('.1.3.6.1.2.1.1.6')
        self.assertIn(
            'Timeout for oid .1.3.6.1.2.1.1.6',
            str(context.exception))

    def test_empty_string(self):
        session = SNMPSession(snmpsim_host, 'public')
        response = session.get('.1.3.6.1.2.1.31.1.1.1.18.1')
        self.assertEqual('', response.typed_value())

    def test_timeticks(self):
        session = SNMPSession(snmpsim_host, 'foreignformats/linux')
        response = session.get('1.3.6.1.2.1.1.3.0').typed_value()
        self.assertIsInstance(response, datetime.timedelta)
        self.assertEqual(14, response.days)

    def test_string(self):
        session = SNMPSession(snmpsim_host, 'public')
        response = session.get('.1.3.6.1.2.1.1.1.0').typed_value()
        self.assertEqual('Linux zeus 4.8.6.5-smp #2 SMP Sun Nov 13 14:58:11 CDT 2016 i686', response)

    def test_int(self):
        session = SNMPSession(snmpsim_host, 'public')
        response = session.get('.1.3.6.1.2.1.1.7.0').typed_value()
        self.assertEqual(72, response)

    def test_counter(self):
        session = SNMPSession(snmpsim_host, 'public')
        response = session.get('.1.3.6.1.2.1.4.10.0').typed_value()
        self.assertEqual(15835620, response)

    def test_gauge(self):
        session = SNMPSession(snmpsim_host, 'public')
        response = session.get('.1.3.6.1.2.1.2.2.1.5.2').typed_value()
        self.assertEqual(100000000, response)

    def test_mac(self):
        session = SNMPSession(snmpsim_host, 'public')
        response = session.get('.1.3.6.1.2.1.2.2.1.6.2').typed_value()
        self.assertEqual('00127962f940', response)

    def test_get_next(self):
        session = SNMPSession(snmpsim_host, 'public')
        response = session.get_next('.1.3.6.1.2.1.1.4.0')
        self.assertEqual('.1.3.6.1.2.1.1.5.0', response.oid)
        self.assertEqual(response.typed_value(), 'zeus.pysnmp.com (you can change this!)')

    def test_walk(self):
        session = SNMPSession(snmpsim_host, 'public')
        response = session.walk('.1.3.6.1.2.1.1')
        self.assertEqual(len(response), 32)
        self.assertEqual(response[31].oid, '.1.3.6.1.2.1.1.9.1.4.8')


if __name__ == '__main__':
    unittest.main()
