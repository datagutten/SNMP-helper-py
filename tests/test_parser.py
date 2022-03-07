import os.path
import unittest

from snmp.mib import MibParser

mib_path = os.path.join(os.path.dirname(__file__), 'mibs')


class ParserTestCase(unittest.TestCase):

    def test_imports(self):
        mib = MibParser.parse_file(mib_path + '/SNMPv2-TC.mib')
        self.assertEqual({'SNMPv2-SMI': ['TimeTicks']}, mib.imports)

    def test_syntax(self):
        mib = MibParser.parse_file(mib_path + '/MG-MIB.mib')
        table = mib.find_node('mgTrapHistoryTable')
        self.assertEqual({'type': 'SEQUENCE', 'object': 'MGTrapHistoryEntry'}, table.syntax)

    def test_identifier(self):
        mib = MibParser.parse_file(mib_path + '/MG-MIB.mib')
        self.assertEqual('mg', mib.identity.root)
        self.assertEqual('MG-MIB', mib.identity.name)
        self.assertEqual('racom', mib.identity.parent)
        self.assertEqual(10, mib.identity.index)

    def test_object_identifier(self):
        mib = MibParser.parse_file(mib_path + '/SNMPv2-MIB.mib')
        node = mib.find_node('system')
        self.assertEqual('mib-2', node.parent)
        self.assertEqual(1, node.index)

    def test_object_identifier2(self):
        # snmp     OBJECT IDENTIFIER ::= { mib-2 11 }
        mib = MibParser.parse_file(mib_path + '/SNMPv2-MIB.mib')
        node_snmp = mib.find_node('snmp')
        self.assertEqual('mib-2', node_snmp.parent)
        self.assertEqual(11, node_snmp.index)


if __name__ == '__main__':
    unittest.main()
