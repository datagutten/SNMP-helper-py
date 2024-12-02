import os
from typing import Dict

from . import MibParser, exceptions
from .objects import MibIdentity, MibNode, MibRawNode, RawMib


class MibTree:
    mibs: Dict[str, RawMib] = {}
    loaded_mibs: list = []
    resolved_mibs: list = []

    def __init__(self):
        iso = MibRawNode(MibIdentity('SNMPv2-SMI', '', 0), 'iso', '', 1)
        self.tree = MibNode(iso, '.1')

    def get_mib(self, mib: str) -> RawMib:
        if mib not in self.mibs:
            raise exceptions.MIBNotFound('Unknown mib %s' % mib)
        else:
            return self.mibs[mib]

    def resolve_imports(self, raw_mib: RawMib):
        """
        Load imported MIBs
        :param raw_mib:
        :return:
        """

        if not raw_mib.imports:
            return  # Provided mib has no imports
        if raw_mib.name in self.loaded_mibs:
            return

        for mib, names in raw_mib.imports.items():
            try:
                mib_obj = self.get_mib(mib)
                if mib_obj.name not in self.loaded_mibs:
                    if mib_obj.imports:
                        self.resolve_imports(mib_obj)
                    else:
                        self.load_mib(mib_obj)
            except exceptions.MIBNotFound:
                print('Imported MIB %s not found' % mib)

        self.resolved_mibs.append(raw_mib.name)
        self.load_mib(raw_mib)

    def find_node(self, name: str, mib=None, start: MibNode = None):
        if type(mib) == MibIdentity:
            mib = mib.name

        if mib and mib not in self.loaded_mibs:
            raise exceptions.MIBNotFound('MIB %s not loaded' % mib)

        if not start:
            start = self.tree

        if start.name == name and (mib is None or start.mib.name == mib):
            return start  # Start node matches

        for node in start.sub_nodes:
            if node.name == name and (mib is None or node.mib.name == mib):
                return node

            try:
                return self.find_node(name, mib, node)
            except exceptions.NodeNotFound:
                pass  # Ignore exceptions from recursive calls

        raise exceptions.NodeNotFound(name, mib)

    def add_node(self, item: MibRawNode, mib: MibIdentity):
        mib = item.mib
        try:  # Check if node is already in the tree
            return self.find_node(item.name, mib)
        except exceptions.NodeNotFound:
            pass  # We need to find the parent before we can add the node

        try:
            parent = self.find_node(item.parent, mib)
        except exceptions.NodeNotFound:  # Parent not in tree
            mib_obj = self.get_mib(mib.name)
            imported = mib_obj.find_import(item.parent)
            if imported:  # Is the parent imported?
                mib_obj_import = self.get_mib(imported)
                raw_parent = mib_obj_import.find_node(item.parent)
                # print('%s is imported to %s from %s' % (item.parent, mib.name, imported))
            else:
                raw_parent = mib_obj.find_node(item.parent)

            parent = self.add_node(raw_parent, mib)

        return parent.add_child(item)

    def mib_depth(self, mib: RawMib):
        # Find root parent and add to tree
        if not mib.identity.parent:
            return 0

        root_node_raw = mib.find_root()
        parent_node = self.find_node(root_node_raw.parent)
        parent_node.add_child(root_node_raw)

        pass

        # try:
        #     node = self.find_node(mib.identity.parent)
        # except exceptions.NodeNotFound as e:
        #     # Parent node not in tree
        #     try:
        #         raw_node = mib.find_node(mib.identity.parent)
        #         node = self.add_node(raw_node, mib.identity)
        #     except exceptions.NodeNotFound:
        #         raise e  # Node not found in the mib, re-raise exception from global search
        #
        # pass

    def load_mib(self, mib: RawMib):
        assert type(mib) == RawMib
        self.loaded_mibs.append(mib.identity.name)
        self.mibs[mib.identity.name] = mib
        self.resolve_imports(mib)
        if mib.identity.parent:
            root_node_raw = mib.find_root()
            if root_node_raw.parent in mib.imported_names:  # Parent is imported
                root_parent_mib = mib.imported_names[root_node_raw.parent]
                parent_node = self.find_node(root_node_raw.parent,
                                             self.get_mib(root_parent_mib).identity)
            else:
                try:  # Try to locate the parent in the current mib
                    parent_node_raw = mib.find_node(root_node_raw.parent)
                    pass
                except exceptions.NodeNotFound as e:
                    raise exceptions.SnmpBrowserException('Root node not found')

            root_node = parent_node.add_child(root_node_raw)
            mib.identity.root = root_node
            # print('Root node %s' % root_node)
        # depth = self.mib_depth(mib)

        for item in mib.nodes:
            try:
                self.add_node(item, mib.identity)
            except exceptions.NodeNotFound as e:
                imported = mib.find_import(item.parent)
                # try:
                if not imported:
                    print('Find parent %s from MIB %s' % (item.parent, mib.identity.name))
                else:
                    print(
                        'Find parent %s imported from MIB %s' % (item.parent, imported))
                try:
                    node = self.find_node(item.parent, imported or mib.identity.name)
                    node.add_child(item)

                except exceptions.NodeNotFound:
                    if not imported:
                        node_raw = mib.find_node(item.parent)
                        self.add_node(node_raw, node_raw.mib)
                    else:
                        imported_mib = self.get_mib(imported)
                        node_raw = imported_mib.find_node(item.parent)
                        self.add_node(node_raw, imported_mib.identity)
                        pass

        return self.tree

    def load_mib_file(self, mib_file):
        mib = MibParser.parse_file(mib_file)
        return self.load_mib(mib)

    def load_mib_folder(self, folder):
        with os.scandir(folder) as scan:
            for mib_file in scan:
                mib = MibParser.parse_file(mib_file)
                self.mibs[mib.identity.name] = mib

        for mib in self.mibs.values():
            self.resolve_imports(mib)

        #     for imported_mib in mib.imports.keys():
        #         try:
        #             imported_mib_obj = self.get_mib(imported_mib)
        #         except exceptions.MIBNotFound as e:
        #             pass
        #
        #     self.load_mib(mib)
