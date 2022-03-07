import os
import unittest

from snmp.mib import MibParser, MibTree, exceptions

mib_path = os.path.join(os.path.dirname(__file__), 'mibs')


class TreeTestCase(unittest.TestCase):
    def test_load(self):
        mib = MibParser.parse_file(mib_path + '/SNMPv2-SMI.mib')
        tree = MibTree()
        tree.load_mib(mib)
        node = tree.find_node('enterprises')
        self.assertEqual('.1.3.6.1.4.1', node.oid)

    def test_load_no_root(self):
        mib = MibParser.parse_file(mib_path + '/MG-MIB.mib')
        tree = MibTree()
        try:
            tree.load_mib(mib)
        except exceptions.NodeNotFound as e:
            self.assertIn('No node named enterprises', str(e))

    def test_load_enterprise(self):
        tree = MibTree()
        tree.load_mib_file(mib_path + '/SNMPv2-SMI.mib')
        tree.load_mib_file(mib_path + '/SNMPv2-MIB.mib')
        tree.load_mib_folder(mib_path)

        node = tree.find_node('wanDialAttempts')
        self.assertEqual('.1.3.6.1.4.1.33555.10.71.1.10', node.oid)
        node2 = tree.find_node('sysName')
        self.assertEqual('.1.3.6.1.2.1.1.5', node2.oid)

    def test_parser_types(self):
        tree = MibTree()
        tree.load_mib_file(mib_path + '/SNMPv2-SMI.mib')
        tree.load_mib_file(mib_path + '/MG-MIB.mib')
        # tree.load_mib_folder(mib_path)

        object_identifier = tree.find_node('midge2')
        self.assertEqual('.1.3.6.1.4.1.33555.10.10.59', object_identifier.oid)
        object_type = tree.find_node('swVersion')
        self.assertEqual('.1.3.6.1.4.1.33555.10.40.1', object_type.oid)
        notification_type = tree.find_node('sms-received')
        self.assertEqual('.1.3.6.1.4.1.33555.10.100.0.603', notification_type.oid)

    def test_load2(self):
        tree = MibTree()
        tree.load_mib_file(mib_path + '/SNMPv2-SMI.mib')
        tree.load_mib_file(mib_path + '/SNMPv2-MIB.mib')
        node = tree.find_node('snmp')
        self.assertEqual('.1.3.6.1.2.1.11', node.oid)


if __name__ == '__main__':
    unittest.main()
