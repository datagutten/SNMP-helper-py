import datetime
import os
import unittest

from snmp_compat import snmp_exceptions, compat

SNMPSession = compat.select(os.getenv('SNMP_LIBRARY'))

print('Running tests with SNMP library %s' % os.getenv('SNMP_LIBRARY'))

snmpsim_host = os.getenv('SNMPSIM_HOST')
snmp_version = int(os.getenv('SNMP_VERSION', 2))
if snmp_version == 3:
    args = {'security_username': 'testing', 'auth_passphrase': 'testing123', 'security_level': 'authNoPriv'}
else:
    args = {}


class SNMPTestCase(unittest.TestCase):

    def test_invalid_oid(self):
        session = SNMPSession(snmpsim_host, 'public')
        with self.assertRaises(snmp_exceptions.SNMPNoData) as context:
            session.get('.1.7.7.7.7')
        self.assertEqual('No data for oid .1.7.7.7.7',
                         str(context.exception))

    def test_connection_error(self):
        if SNMPSession.__name__ == 'EZSNMP2Compat':
            self.skipTest('ezsnmp does not throw exception on connect')
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

    def test_timeout_3sec(self):
        start = datetime.datetime.now()
        with self.assertRaises(snmp_exceptions.SNMPTimeout) as context:
            session = SNMPSession(snmpsim_host, 'ciscobad', timeout=3)
            session.get('.1.3.6.1.2.1.1.6')
        self.assertIn(
            'Timeout for oid .1.3.6.1.2.1.1.6',
            str(context.exception))
        diff = datetime.datetime.now() - start
        self.assertGreaterEqual(diff.seconds, 3)

    def test_empty_string(self):
        session = SNMPSession(snmpsim_host, 'public', **args)
        response = session.get('.1.3.6.1.2.1.31.1.1.1.18.1')
        self.assertEqual('', response.typed_value())

    def test_timeticks(self):
        session = SNMPSession(snmpsim_host, 'foreignformats/linux', **args)
        response = session.get('1.3.6.1.2.1.1.3.0').typed_value()
        self.assertIsInstance(response, datetime.timedelta)
        self.assertEqual(14, response.days)

    def test_string(self):
        session = SNMPSession(snmpsim_host, 'public', **args)
        response = session.get('.1.3.6.1.2.1.1.1.0').typed_value()
        self.assertEqual('Linux zeus 4.8.6.5-smp #2 SMP Sun Nov 13 14:58:11 CDT 2016 i686', response)

    # def test_string_v3(self):
    #     session = SNMPSession.connect_v3(snmpsim_host, 'public', 'testing', 'testing123')
    #     response = session.get('.1.3.6.1.2.1.1.1.0').typed_value()
    #     self.assertEqual('Linux zeus 4.8.6.5-smp #2 SMP Sun Nov 13 14:58:11 CDT 2016 i686', response)

    def test_int(self):
        session = SNMPSession(snmpsim_host, 'public', **args)
        response = session.get('.1.3.6.1.2.1.1.7.0').typed_value()
        self.assertEqual(72, response)

    def test_counter(self):
        session = SNMPSession(snmpsim_host, 'public', **args)
        response = session.get('.1.3.6.1.2.1.4.10.0').typed_value()
        self.assertEqual(15835620, response)

    def test_gauge(self):
        session = SNMPSession(snmpsim_host, 'public', **args)
        response = session.get('.1.3.6.1.2.1.2.2.1.5.2').typed_value()
        self.assertEqual(100000000, response)

    def test_mac(self):
        session = SNMPSession(snmpsim_host, 'public', **args)
        response = session.get('.1.3.6.1.2.1.2.2.1.6.2')
        self.assertEqual('00127962f940', response.hex_string())
        self.assertEqual('00127962f940', response.typed_value())

    def test_ip(self):
        session = SNMPSession(snmpsim_host, 'public', **args)
        response = session.get_next('.1.3.6.1.2.1.4.20.1.1')
        self.assertEqual('127.0.0.1', response.ip_address())
        self.assertEqual('127.0.0.1', response.typed_value())

    def test_cdp_ip(self):
        session = SNMPSession(snmpsim_host, 'cisco', **args)
        response = session.get('.1.3.6.1.4.1.9.9.23.1.2.1.1.4.10122.4')
        self.assertEqual('10.0.2.242', response.ip_address())

    def test_get_next(self):
        session = SNMPSession(snmpsim_host, 'public', **args)
        response = session.get_next('.1.3.6.1.2.1.1.4.0')
        self.assertEqual('.1.3.6.1.2.1.1.5.0', response.oid)
        self.assertEqual(response.typed_value(), 'zeus.pysnmp.com (you can change this!)')

    def test_walk(self):
        session = SNMPSession(snmpsim_host, 'public', **args)
        response = session.walk('.1.3.6.1.2.1.1')
        self.assertEqual(len(response), 32)
        self.assertEqual(response[31].oid, '.1.3.6.1.2.1.1.9.1.4.8')

    def test_multiline(self):
        session = SNMPSession(snmpsim_host, 'cisco', **args)
        response = session.get('.1.3.6.1.2.1.1.1.0')
        desc = (
            "Cisco IOS Software, C2960S Software (C2960S-UNIVERSALK9-M), Version 15.0(2)SE11, RELEASE SOFTWARE (fc3)\r\n"
            "Technical Support: http://www.cisco.com/techsupport\r\nCopyright (c) 1986-2017 by Cisco Systems, Inc.\r\n"
            "Compiled Sat 19-Aug-17 08:57 by prod_rel_team")
        self.assertEqual(response.typed_value(), desc)

    def test_select(self):
        lib = compat.select()
        self.assertIsInstance(lib, type(compat.SNMPCompat))

    def test_select_invalid(self):
        with self.assertRaises(AttributeError) as context:
            compat.select('bad')
        self.assertEqual('Invalid library bad', str(context.exception))

    def test_select_none(self):
        with self.assertRaises(AttributeError) as context:
            del os.environ['SNMP_LIBRARY']
            compat.select(None)
        self.assertEqual('library argument not set and SNMP_LIBRARY environment variable not set',
                         str(context.exception))

    def test_bytes(self):
        session = SNMPSession(snmpsim_host, 'cisco', **args)
        response = session.get_next('.1.3.6.1.4.1.9.9.46.1.6.1.1.4')
        self.assertEqual(bytes(response)[0], 0x7f)
        self.assertEqual(bytes(response)[1], 0xff)


if __name__ == '__main__':
    unittest.main()
