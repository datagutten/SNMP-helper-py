import warnings
from typing import Dict, List

from . import exceptions


class MibIdentity:
    name: str
    root: str
    parent: str
    index: int

    def __init__(self, name, root=None, parent=None, index=None):
        self.name = name
        self.root = root
        self.parent = parent
        self.index = index


class RawMib:
    imports: Dict[str, List] = []
    imported_names = {}
    identity: MibIdentity

    def __init__(self, identity: MibIdentity):
        self.name: str = identity.name
        self.identity = identity
        self.nodes: List[MibRawNode] = []

    def add_item(self, name: str, parent: str, index: int):
        warnings.warn("Deprecated", DeprecationWarning)
        raw_node = MibRawNode(self.identity, name, parent, index)
        self.nodes.append(raw_node)

    def add_node(self, node: 'MibRawNode'):
        if node.parent == '0':
            return
        self.nodes.append(node)

    def find_node(self, name) -> 'MibRawNode':
        """Finds a node based on its name, returns RawMibItem"""
        for item in self.nodes:
            if item.name == name:
                return item
        raise exceptions.NodeNotFound(name, self.identity)

    def find_root(self) -> 'MibRawNode':
        for item in self.nodes:
            try:
                self.find_node(item.parent)
            except exceptions.NodeNotFound:
                return item
        raise exceptions.MIBParseError('All MIB nodes have parent in current mib')

    def find_import(self, name):
        """
        Check if the name is imported and return the MIB name
        :param name:
        :return:
        """
        if name in self.imported_names:
            return self.imported_names[name]

    def __str__(self):
        return 'MIB: %s' % self.name


class RawMibItem:
    warnings.warn("Deprecated", DeprecationWarning)

    def __init__(self, name: str, parent: str, index: int, mib_name: str, access: str = None,
                 description: str = None, mib_obj: RawMib = None):
        warnings.warn("Deprecated", DeprecationWarning)
        self.name: str = name
        self.parent: str = parent
        self.index: int = index
        self.mib_name: str = mib_name
        self.access: str = access
        self.description: str = description
        self.mib: RawMib = mib_obj

    def __str__(self):
        return '%s::%s' % (self.mib_name, self.name)


class MibRawNode:
    def __init__(self, mib: MibIdentity, name: str, parent: str, index: int,
                 access: str = None,
                 description: str = None,
                 syntax: str = None):
        assert type(mib) == MibIdentity
        assert type(index) == int

        self.mib: MibIdentity = mib
        self.name: str = name
        self.parent: str = parent
        self.index: int = index
        self.access: str = access
        self.description: str = description
        self.syntax: str = syntax

    def __str__(self):
        return '%s::%s' % (self.mib_name, self.name)

    @property
    def mib_name(self):
        return self.mib.name


class MibNode:
    sub_nodes = List['MibNode']

    def __init__(self, node: MibRawNode, oid):
        self.name: str = node.name
        self.mib: MibIdentity = node.mib
        self.oid: str = oid
        self.sub_nodes = []
        self.raw_node: MibRawNode = node

    def add_child(self, node: MibRawNode):
        oid = '%s.%d' % (self.oid, node.index)
        sub_node = MibNode(node, oid)
        self.sub_nodes.append(sub_node)
        self.sub_nodes.sort(key=lambda node_obj: node_obj.raw_node.index)
        return sub_node

    @property
    def depth(self):
        return len(self.oid.split('.'))

    def __str__(self):
        return '%s::%s' % (self.mib.name, self.name)
