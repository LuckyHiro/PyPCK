# - "Normal" pck packs are just what I think of as the default when it comes to legacy console. 
# - It includes Xbox 360, PS3, WII U, and the leaked windows64 build if you are using that
 
import os
import random
import struct

ASSET_SKIN = 0
ASSET_CAPE = 1
ASSET_INFO = 4
ASSET_LOCALISATION = 6

PCK_TYPE = 3
LOC_VERSION = 2

ANIM_MODERN_WIDE_MODEL = 1 << 18

MAX_PACK_ID = 0xFFFFFF
MIN_PACK_ID = 8000

MIN_SKIN_ID = 100000
MAX_SKIN_ID = 99999999


def _be32(value):
    return struct.pack(">i", value)


def _be16(value):
    return struct.pack(">h", value)


def _i32(value, little_endian=False):
    return struct.pack("<i" if little_endian else ">i", value)


def _pck_string(text, little_endian=False):
    codec = "utf-16-le" if little_endian else "utf-16-be"
    encoded = text.encode(codec)
    return _i32(len(encoded) // 2, little_endian) + encoded + _i32(0, little_endian)


def _loc_string(text):
    encoded = text.encode("utf-8")
    return _be16(len(encoded)) + encoded


def build_loc_file(pack_name, skin_names):
    languages = ["en-EN"]

    loc_keys = {"IDS_DISPLAY_NAME": {"en-EN": pack_name}}
    for skin_id, name in skin_names.items():
        loc_keys[f"IDS_dlcskin{skin_id:08d}_DISPLAYNAME"] = {"en-EN": name}

    out = bytearray()
    out += _be32(LOC_VERSION)
    out += _be32(len(languages))
    out += b"\x00"
    out += _be32(len(loc_keys))
    for key in loc_keys:
        out += _loc_string(key)

    for lang in languages:
        entry_size = (
            4
            + 1
            + 2 + len(lang.encode("utf-8"))
            + 4
            + sum(2 + len(loc_keys[k][lang].encode("utf-8")) for k in loc_keys)
        )
        out += _loc_string(lang)
        out += _be32(entry_size)

    for lang in languages:
        out += _be32(LOC_VERSION)
        out += b"\x00"
        out += _loc_string(lang)
        out += _be32(len(loc_keys))
        for key in loc_keys:
            out += _loc_string(loc_keys[key][lang])

    return bytes(out)


class PckAsset:
    __slots__ = ("filename", "type", "params", "data")

    def __init__(self, filename, asset_type, params=None, data=b""):
        self.filename = filename
        self.type = asset_type
        self.params = params or []
        self.data = data


def write_pck(assets, output_path, little_endian=False):
    lut = []
    lut_index = {}
    for asset in assets:
        for key, _ in asset.params:
            if key not in lut_index:
                lut_index[key] = len(lut)
                lut.append(key)

    out = bytearray()
    out += _i32(PCK_TYPE, little_endian)
    out += _i32(len(lut), little_endian)
    for i, key in enumerate(lut):
        out += _i32(i, little_endian)
        out += _pck_string(key, little_endian)

    out += _i32(len(assets), little_endian)
    for asset in assets:
        out += _i32(len(asset.data), little_endian)
        out += _i32(asset.type, little_endian)
        out += _pck_string(asset.filename, little_endian)

    for asset in assets:
        out += _i32(len(asset.params), little_endian)
        for key, value in asset.params:
            out += _i32(lut_index[key], little_endian)
            out += _pck_string(value, little_endian)
        out += asset.data

    with open(output_path, "wb") as f:
        f.write(out)


def build_info_asset(pack_id):
    return PckAsset(
        filename="0",
        asset_type=ASSET_INFO,
        params=[("PACKID", str(pack_id)), ("PACKVERSION", "0")],
    )


def build_skin_asset(skin_png, display_name, skin_id, has_cape, anim_flags):
    filename = f"dlcskin{skin_id:08d}.png"
    loc_key = f"IDS_dlcskin{skin_id:08d}_DISPLAYNAME"

    params = [
        ("DISPLAYNAME", display_name),
        ("DISPLAYNAMEID", loc_key),
    ]
    if has_cape:
        params.append(("CAPEPATH", f"dlccape{skin_id:08d}.png"))
    params += [
        ("ANIM", f"0x{anim_flags:08x}"),
        ("GAME_FLAGS", "0x00"),
        ("FREE", "1"),
    ]

    return PckAsset(filename=filename, asset_type=ASSET_SKIN,
                    params=params, data=skin_png)


def build_cape_asset(cape_png, skin_id):
    return PckAsset(
        filename=f"dlccape{skin_id:08d}.png",
        asset_type=ASSET_CAPE,
        data=cape_png,
    )


def get_png_size(path):
    with open(path, "rb") as f:
        header = f.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Not a valid PNG file: {path}")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def default_anim_flags(skin_path):
    width, height = get_png_size(skin_path)
    return ANIM_MODERN_WIDE_MODEL if width == height else 0


def is_valid_cape(path):
    width, height = get_png_size(path)
    return width == height * 2


def iter_cape_files(capes_folder):
    for entry in sorted(os.listdir(capes_folder)):
        full = os.path.join(capes_folder, entry)
        if os.path.isfile(full) and entry.lower().endswith(".png"):
            yield full


def _unique_skin_id(used_ids, rng):
    while True:
        skin_id = rng.randint(MIN_SKIN_ID, MAX_SKIN_ID)
        if skin_id not in used_ids:
            used_ids.add(skin_id)
            return skin_id


def build_skin_pack(skin_path, capes_folder, output_path,
                    pack_name=None, pack_id=None, seed=None,
                    little_endian=False):
    if os.path.isdir(output_path):
        output_path = os.path.join(output_path, "SkinPack.pck")

    rng = random.Random(seed)

    if pack_name is None:
        pack_name = os.path.splitext(os.path.basename(skin_path))[0]
    if pack_id is None:
        pack_id = rng.randint(MIN_PACK_ID, MAX_PACK_ID)

    with open(skin_path, "rb") as f:
        skin_png = f.read()
    anim_flags = default_anim_flags(skin_path)

    used_ids = set()
    skin_names = {}
    assets = [build_info_asset(pack_id)]

    skin_entries = []
    if capes_folder is None:
        skin_id = _unique_skin_id(used_ids, rng)
        skin_names[skin_id] = pack_name
        skin_entries.append((skin_id, pack_name, None))
    else:
        for cape_path in iter_cape_files(capes_folder):
            if not is_valid_cape(cape_path):
                print(f"Skipping invalid cape (must be 2:1 width:height): {cape_path}")
                continue
            with open(cape_path, "rb") as f:
                cape_png = f.read()

            skin_id = _unique_skin_id(used_ids, rng)
            display_name = os.path.splitext(os.path.basename(cape_path))[0]

            skin_names[skin_id] = display_name
            skin_entries.append((skin_id, display_name, cape_png))

    loc_data = build_loc_file(pack_name, skin_names)
    assets.append(PckAsset(filename="localisation.loc",
                           asset_type=ASSET_LOCALISATION, data=loc_data))

    for skin_id, display_name, cape_png in skin_entries:
        assets.append(build_skin_asset(skin_png, display_name, skin_id,
                                       has_cape=cape_png is not None,
                                       anim_flags=anim_flags))
        if cape_png is not None:
            assets.append(build_cape_asset(cape_png, skin_id))

    write_pck(assets, output_path, little_endian=little_endian)
    return output_path


def handle_new_pack(answers):
    from .LittleEndianPacks import build_little_endian_skin_pack

    if answers["platform"] == "2":
        output_path = build_little_endian_skin_pack(
            answers["skin_path"],
            answers["capes_folder"],
            answers["output_path"],
        )
    else:
        output_path = build_skin_pack(
            answers["skin_path"],
            answers["capes_folder"],
            answers["output_path"],
        )
    print(f"Skin pack written to {output_path}")
