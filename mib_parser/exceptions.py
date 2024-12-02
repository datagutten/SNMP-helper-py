from .objects import MibIdentity


class SnmpBrowserException(ValueError):
    pass


class MIBParseError(SnmpBrowserException):
    pass


class NodeNotFound(SnmpBrowserException):
    def __init__(self, name: str, mib=None):
        if type(mib) == MibIdentity:
            mib = mib.name

        if not mib:
            msg = 'No node named %s in any MIB in the tree' % name
        else:
            msg = 'No node named %s in %s' % (name, mib)

        super(NodeNotFound, self).__init__(msg)


class MIBNotFound(SnmpBrowserException):
    pass
