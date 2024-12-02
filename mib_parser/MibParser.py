import re

from . import exceptions
from .objects import MibIdentity, MibRawNode, RawMib


def parse_imports(mib):
    mib_imports = {}
    matches = re.search(r'IMPORTS\s+(.+?);', mib, re.DOTALL)
    if not matches:
        return None, None  # No imports
    imports = matches.group(1)
    imported_names = {}
    for matches in re.finditer(r'(.+?)FROM (.+?)(?:\s|$)', imports, re.DOTALL):
        import_from = matches.group(2)
        imported = re.findall(r'([\w\-]+)', matches.group(1))
        if import_from not in mib_imports:
            mib_imports[import_from] = imported
        else:
            mib_imports[import_from] += imported
        for name in imported:
            imported_names[name] = import_from

    return mib_imports, imported_names


def parse_macros(mib):
    macros = {}
    for matches in re.finditer(r'([\w\-]+) MACRO\s::=\sBEGIN\s*(.+?)\s*END', mib, re.DOTALL):
        macros[matches.group(1)] = matches.group(2)
    return macros


parent_identifier = r'\s*::=\s*{\s*([\w\-]+)\s*([0-9]+)\s*}'


def parse_identifiers(mib_content: str, mib: RawMib):
    for matches in re.finditer(
            r'([\w\-]+)\s*OBJECT IDENTIFIER' + parent_identifier, mib_content):
        item = MibRawNode(
            mib=mib.identity,
            name=matches.group(1),
            parent=matches.group(2),
            index=int(matches.group(3)),
        )
        mib.add_node(item)


def parse_identity(mib: str):
    matches_name = re.search(r'([\w+-]+) DEFINITIONS ::= BEGIN', mib)
    if not matches_name:
        raise exceptions.MIBParseError('MIB name not found')

    matches = re.search(r'([\w\-]+)\sMODULE-IDENTITY\s*(.+?)' + parent_identifier, mib, re.DOTALL)
    if not matches:
        return MibIdentity(name=matches_name.group(1))
    else:
        return MibIdentity(name=matches_name.group(1),
                           root=matches.group(1),
                           parent=matches.group(3),
                           index=int(matches.group(4)))


def parse_object_types(mib_content: str, mib: RawMib):
    nodes = []
    for matches in re.finditer(r'([\w\-]+)\s*OBJECT-TYPE(.+?)' + parent_identifier, mib_content,
                               re.DOTALL):
        item = MibRawNode(
            mib=mib.identity,
            name=matches.group(1),
            parent=matches.group(3),
            index=int(matches.group(4)),
        )
        content = matches.group(2)
        properties = {}
        for matches_value in re.finditer(r'([\w\-]+)\s+(.+)', content):
            key = matches_value.group(1)
            value = matches_value.group(2)
            properties[key] = value

        if 'SYNTAX' in properties:
            matches_sequence = re.match(r'SEQUENCE OF ([\w\-]+)', properties['SYNTAX'])
            if matches_sequence:
                item.syntax = {
                    'type': 'SEQUENCE',
                    'object': matches_sequence.group(1)
                }
            else:
                item.syntax = properties['SYNTAX']
        if 'MAX-ACCESS' in properties:
            item.access = properties['MAX-ACCESS']
        if 'STATUS' in properties:
            item.status = properties['STATUS']
        if 'DESCRIPTION' in properties:
            item.description = properties['DESCRIPTION']

        mib.add_node(item)

    return nodes


class MibParser:
    @staticmethod
    def parse_file(file) -> RawMib:
        parser = MibParser()
        with open(file) as fp:
            return parser.parse_mib(fp.read())

    def parse_mib(self, mib_content: str) -> RawMib:
        name_waiting = None
        prev_line = None
        more_needed = False

        identity = parse_identity(mib_content)
        mib = RawMib(identity)
        parse_object_types(mib_content, mib)
        parse_identifiers(mib_content, mib)

        for line in mib_content.splitlines():
            line = line.strip()
            cols = line.split()
            if name_waiting:
                if "::=" not in line:
                    continue
                name = name_waiting
                name_waiting = None
                match = re.search(r"::=\s*\{\s*([\w-]+)\s+([0-9]+)\s*\}", line)
                # Added to the tree later below
                item = MibRawNode(mib=mib.identity,
                                  name=name,
                                  parent=match[1],
                                  index=int(match[2])
                                  )
                mib.add_node(item)

            elif line == "" or line.startswith("--") or line.find(",") >= 0 or cols[0] == "SYNTAX":
                continue
            elif (
                    len(cols) == 2 and cols[1] in [
                "OBJECT-IDENTITY",
                "OBJECT-TYPE",
                "MODULE-IDENTITY",
                "NOTIFICATION-TYPE",
            ]) or (
                    len(cols) == 3 and cols[1] == "OBJECT" and cols[2] == "IDENTIFIER"
            ):
                # Save the name and keep looping
                name_waiting = cols[0]
                continue
            elif more_needed:
                line = prev_line + " " + line
                more_needed = False
            elif line.startswith("IMPORTS"):
                continue
            else:
                prev_line = line
                continue

        mib.imports, mib.imported_names = parse_imports(mib_content)
        return mib
