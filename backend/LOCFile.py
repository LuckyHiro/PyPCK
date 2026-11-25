import struct


def _be32(v):
    return struct.pack(">i", v)


def _be16(v):
    return struct.pack(">h", v)


def _loc_string(text):
    encoded = text.encode("utf-8")
    return _be16(len(encoded)) + encoded


class LocFile:
    def __init__(self, version, has_uids, languages, keys):
        self.version = version
        self.has_uids = has_uids
        self.languages = languages
        self.keys = keys


def parse_loc_file(data):
    pos = 0

    def i32():
        nonlocal pos
        v = struct.unpack_from(">i", data, pos)[0]
        pos += 4
        return v

    def loc_str():
        nonlocal pos
        length = struct.unpack_from(">h", data, pos)[0]
        pos += 2
        s = data[pos:pos + length].decode("utf-8")
        pos += length
        return s

    version = i32()
    language_count = i32()
    look_up_keys = version == 2

    has_uids = False
    key_list = None
    if look_up_keys:
        has_uids = data[pos] != 0
        pos += 1
        key_count = i32()
        key_list = []
        for _ in range(key_count):
            if has_uids:
                key_list.append(f"{i32() & 0xFFFFFFFF:08X}")
            else:
                key_list.append(loc_str())

    languages = []
    entry_sizes = []
    for _ in range(language_count):
        languages.append(loc_str())
        entry_sizes.append(i32())

    keys = {}
    for lang, size in zip(languages, entry_sizes):
        entry = data[pos:pos + size]
        pos += size

        epos = 0

        def ei32():
            nonlocal epos
            v = struct.unpack_from(">i", entry, epos)[0]
            epos += 4
            return v

        def eloc_str():
            nonlocal epos
            length = struct.unpack_from(">h", entry, epos)[0]
            epos += 2
            s = entry[epos:epos + length].decode("utf-8")
            epos += length
            return s

        entry_version = ei32()
        if entry_version > 0:
            epos += 1
        entry_lang = eloc_str()
        key_count = ei32()

        for j in range(key_count):
            if look_up_keys:
                key = key_list[j]
            else:
                key = eloc_str()
            value = eloc_str()
            keys.setdefault(key, {})[entry_lang] = value

    return LocFile(version, has_uids, languages, keys)


def write_loc_file(loc):
    out = bytearray()
    out += _be32(loc.version)
    out += _be32(len(loc.languages))

    if loc.version == 2:
        out += b"\x01" if loc.has_uids else b"\x00"
        out += _be32(len(loc.keys))
        for key in loc.keys:
            if loc.has_uids:
                out += _be32(int(key, 16))
            else:
                out += _loc_string(key)

    for lang in loc.languages:
        entry_size = (
            4
            + (1 if loc.version > 0 else 0)
            + 2 + len(lang.encode("utf-8"))
            + 4
            + sum(
                (2 + len(key.encode("utf-8")) if loc.version == 0 else 0)
                + 2 + len(loc.keys[key].get(lang, "").encode("utf-8"))
                for key in loc.keys
            )
        )
        out += _loc_string(lang)
        out += _be32(entry_size)

    for lang in loc.languages:
        out += _be32(loc.version)
        if loc.version > 0:
            out += b"\x01" if loc.has_uids else b"\x00"
        out += _loc_string(lang)
        out += _be32(len(loc.keys))
        for key in loc.keys:
            if loc.version == 0:
                out += _loc_string(key)
            out += _loc_string(loc.keys[key].get(lang, ""))

    return bytes(out)


def add_loc_entries(loc, new_entries):
    for key, value in new_entries.items():
        if key in loc.keys:
            continue
        loc.keys[key] = {lang: value for lang in loc.languages}


def set_loc_entries(loc, entries):
    for key, value in entries.items():
        loc.keys[key] = {lang: value for lang in loc.languages}
