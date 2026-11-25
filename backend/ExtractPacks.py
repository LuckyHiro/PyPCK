import os

from .PCKReader import read_pck, ASSET_SKIN, ASSET_CAPE, ASSET_INFO, ASSET_LOCALISATION
from .Questions import _clean_path

ASSET_TYPE_NAMES = {
    0: "SkinFile",
    1: "CapeFile",
    2: "TextureFile",
    3: "UIDataFile",
    4: "InfoFile",
    5: "TexturePackInfoFile",
    6: "LocalisationFile",
    7: "GameRulesFile",
    8: "AudioFile",
    9: "ColourTableFile",
    10: "GameRulesHeader",
    11: "SkinDataFile",
    12: "ModelsFile",
    13: "BehavioursFile",
    14: "MaterialFile",
}


def _asset_type_name(asset_type):
    return ASSET_TYPE_NAMES.get(asset_type, f"Unknown({asset_type})")


def _write_pack_info(pck, info_path):
    lines = []
    lines.append(f"Pack: {os.path.basename(pck.path)}")
    lines.append(f"Endianness: {'little' if pck.little_endian else 'big'}")
    lines.append(f"Asset count: {len(pck.assets)}")
    lines.append("")
    lines.append("Assets:")
    for asset in pck.assets:
        lines.append(f"  {asset.filename} ({_asset_type_name(asset.type)}, {len(asset.data)} bytes)")
        for key, value in asset.params:
            lines.append(f"    {key} = {value}")

    skins = pck.get_skins()
    lines.append("")
    lines.append(f"Skins ({len(skins)}):")
    for skin in skins:
        lines.append(f"  {skin['filename']}")
        lines.append(f"    ID: {skin['id']}")
        lines.append(f"    Name: {skin['name']}")
        lines.append(f"    ANIM: {skin['anim']}")
        lines.append(f"    GAME_FLAGS: {skin['game_flags']}")
        lines.append(f"    Texture: {len(skin['texture'])} bytes")
        if skin["cape"] is not None:
            lines.append(f"    Cape: {len(skin['cape'])} bytes")
        else:
            lines.append("    Cape: none")

    with open(info_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def extract_all(pck_path, extract_dir):
    pck = read_pck(pck_path)
    os.makedirs(extract_dir, exist_ok=True)

    for asset in pck.assets:
        out_path = os.path.join(extract_dir, asset.filename)
        os.makedirs(os.path.dirname(out_path) or extract_dir, exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(asset.data)

    info_path = os.path.join(extract_dir, "pack_info.txt")
    _write_pack_info(pck, info_path)

    return extract_dir


def extract_skin(pck, skin_index, output_dir):
    skin = pck.get_skins()[skin_index]
    os.makedirs(output_dir, exist_ok=True)

    skin_path = os.path.join(output_dir, skin["filename"])
    with open(skin_path, "wb") as f:
        f.write(skin["texture"])

    cape_path = None
    if skin["cape"] is not None:
        capepath = skin["asset"].get_param("CAPEPATH")
        cape_path = os.path.join(output_dir, capepath or f"dlccape{skin['id']:08d}.png")
        with open(cape_path, "wb") as f:
            f.write(skin["cape"])

    lines = [
        f"Pack: {os.path.basename(pck.path)}",
        f"Endianness: {'little' if pck.little_endian else 'big'}",
        "",
        f"Skin file: {skin['filename']}",
        f"ID: {skin['id']}",
        f"Name: {skin['name']}",
        f"ANIM: {skin['anim']}",
        f"GAME_FLAGS: {skin['game_flags']}",
        f"Texture: {len(skin['texture'])} bytes -> {os.path.basename(skin_path)}",
    ]
    if cape_path:
        lines.append(f"Cape: {len(skin['cape'])} bytes -> {os.path.basename(cape_path)}")
    else:
        lines.append("Cape: none")
    lines.append("")
    lines.append("Parameters:")
    for key, value in skin["asset"].params:
        lines.append(f"  {key} = {value}")

    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in skin["name"]).strip() or f"skin_{skin['id']}"
    info_path = os.path.join(output_dir, f"{safe_name}_info.txt")
    with open(info_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return skin_path, cape_path, info_path


def ask_extract_skin(skins):
    print("Skins in pack:")
    for i, skin in enumerate(skins):
        print(f"- {i}: {skin['name']} (ID: {skin['id']})")
    skin_index = int(input("Enter the skin number: ").strip())
    output_dir = _clean_path(input("Enter the folder to extract into: "))
    return {"skin_index": skin_index, "output_dir": output_dir}


def handle_extract(answers):
    if answers["extract_mode"] == "1":
        extract_all(answers["pck_path"], answers["extract_dir"])
        print(f"Extracted to {answers['extract_dir']}")
        return

    pck = read_pck(answers["pck_path"])
    skins = pck.get_skins()
    if not skins:
        print("No skins found in that pack.")
        return
    sel = ask_extract_skin(skins)
    extract_skin(pck, sel["skin_index"], sel["output_dir"])
    print(f"Extracted to {sel['output_dir']}")
