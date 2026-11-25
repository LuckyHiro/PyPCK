import struct

ASSET_SKIN = 0
ASSET_CAPE = 1
ASSET_INFO = 4
ASSET_LOCALISATION = 6


class PckAsset:
    __slots__ = ("filename", "type", "params", "data")

    def __init__(self, filename, asset_type, params=None, data=b""):
        self.filename = filename
        self.type = asset_type
        self.params = params or []
        self.data = data

    def get_param(self, key, default=None):
        for k, v in self.params:
            if k == key:
                return v
        return default


class PckFile:
    __slots__ = ("assets", "little_endian", "path")

    def __init__(self, assets, little_endian, path):
        self.assets = assets
        self.little_endian = little_endian
        self.path = path

    def get_assets_by_type(self, asset_type):
        return [a for a in self.assets if a.type == asset_type]

    def get_skins(self):
        skins = []
        for asset in self.get_assets_by_type(ASSET_SKIN):
            skin_id_str = asset.filename[len("dlcskin"):-len(".png")]
            try:
                skin_id = int(skin_id_str)
            except ValueError:
                skin_id = None

            capepath = asset.get_param("CAPEPATH")
            cape_asset = None
            if capepath:
                for other in self.assets:
                    if other.filename == capepath and other.type == ASSET_CAPE:
                        cape_asset = other
                        break

            skins.append({
                "id": skin_id,
                "filename": asset.filename,
                "name": asset.get_param("DISPLAYNAME", ""),
                "anim": asset.get_param("ANIM", ""),
                "game_flags": asset.get_param("GAME_FLAGS", ""),
                "texture": asset.data,
                "cape": cape_asset.data if cape_asset else None,
                "asset": asset,
            })
        return skins


def _i32(data, pos, little_endian):
    fmt = "<i" if little_endian else ">i"
    return struct.unpack_from(fmt, data, pos)[0], pos + 4


def _pck_string(data, pos, little_endian):
    char_count, pos = _i32(data, pos, little_endian)
    codec = "utf-16-le" if little_endian else "utf-16-be"
    raw = data[pos:pos + char_count * 2]
    pos += char_count * 2
    pos += 4
    return raw.decode(codec), pos


def _parse_pck(data, little_endian):
    pos = 0

    pck_type, pos = _i32(data, pos, little_endian)
    if pck_type < 3 or pck_type > 0x00F00000:
        raise ValueError(f"Invalid PCK type: {pck_type}")

    lut_count, pos = _i32(data, pos, little_endian)
    if lut_count < 0 or lut_count > 100000:
        raise ValueError(f"Invalid parameter count: {lut_count}")

    lut = []
    for _ in range(lut_count):
        _, pos = _i32(data, pos, little_endian)
        value, pos = _pck_string(data, pos, little_endian)
        lut.append(value)

    asset_count, pos = _i32(data, pos, little_endian)
    if asset_count < 0 or asset_count > 100000:
        raise ValueError(f"Invalid asset count: {asset_count}")

    entries = []
    for _ in range(asset_count):
        size, pos = _i32(data, pos, little_endian)
        asset_type, pos = _i32(data, pos, little_endian)
        filename, pos = _pck_string(data, pos, little_endian)
        if size < 0:
            raise ValueError(f"Invalid asset size: {size}")
        entries.append((filename, asset_type, size))

    assets = []
    for filename, asset_type, size in entries:
        param_count, pos = _i32(data, pos, little_endian)
        if param_count < 0 or param_count > 10000:
            raise ValueError(f"Invalid parameter count on asset {filename}")
        params = []
        for _ in range(param_count):
            lut_index, pos = _i32(data, pos, little_endian)
            if lut_index < 0 or lut_index >= len(lut):
                raise ValueError(f"Parameter index out of range on asset {filename}")
            value, pos = _pck_string(data, pos, little_endian)
            params.append((lut[lut_index], value))
        payload = data[pos:pos + size]
        pos += size
        assets.append(PckAsset(filename, asset_type, params, payload))

    return assets


def read_pck(path):
    with open(path, "rb") as f:
        data = f.read()

    try:
        assets = _parse_pck(data, little_endian=True)
        return PckFile(assets, little_endian=True, path=path)
    except (ValueError, struct.error, UnicodeDecodeError):
        pass

    assets = _parse_pck(data, little_endian=False)
    return PckFile(assets, little_endian=False, path=path)
