import os
import random

from .PCKReader import read_pck, ASSET_SKIN, ASSET_CAPE, ASSET_LOCALISATION
from .LOCFile import parse_loc_file, write_loc_file, add_loc_entries, set_loc_entries
from .Questions import _clean_path


def ask_skin_edit(skins):
    print("Skins in pack:")
    for i, skin in enumerate(skins):
        print(f"- {i}: {skin['name']} (ID: {skin['id']})")
    skin_index = int(input("Enter the skin number: ").strip())

    print("What do you want to do?")
    print("- 1: Replace Skin")
    print("- 2: Replace Cape")
    print("- 3: Remove Cape")
    print("- 4: Delete Skin")
    print("- 5: Change Name")
    operation = input("Enter an option: ").strip()

    result = {"skin_index": skin_index, "operation": operation}
    if operation == "1":
        result["file_path"] = _clean_path(input("Enter the path to the new skin image: "))
    elif operation == "2":
        result["file_path"] = _clean_path(input("Enter the path to the new cape image: "))
    elif operation == "5":
        result["new_name"] = input("Enter the new name: ").strip()
    return result
from .NormalPacks import (
    build_skin_asset,
    build_cape_asset,
    default_anim_flags,
    is_valid_cape,
    iter_cape_files,
    write_pck,
    _unique_skin_id,
)


def _existing_skin_ids(pck):
    ids = set()
    for asset in pck.assets:
        if asset.type == ASSET_SKIN and asset.filename.startswith("dlcskin") and asset.filename.endswith(".png"):
            try:
                ids.add(int(asset.filename[len("dlcskin"):-len(".png")]))
            except ValueError:
                pass
    return ids


def _iter_skin_files(skins_folder):
    for entry in sorted(os.listdir(skins_folder)):
        full = os.path.join(skins_folder, entry)
        if os.path.isfile(full) and entry.lower().endswith(".png"):
            yield full


def _skin_display_name(path):
    return os.path.splitext(os.path.basename(path))[0]


def add_to_pack(pck_path, output_path, add_mode,
                skin_path=None, skins_folder=None, capes_folder=None,
                seed=None):
    pck = read_pck(pck_path)

    if os.path.isdir(output_path):
        output_path = os.path.join(output_path, os.path.basename(pck_path))

    rng = random.Random(seed)
    used_ids = _existing_skin_ids(pck)
    assets = list(pck.assets)

    entries = []

    if add_mode == "1":
        with open(skin_path, "rb") as f:
            skin_png = f.read()
        anim_flags = default_anim_flags(skin_path)

        for cape_path in iter_cape_files(capes_folder):
            if not is_valid_cape(cape_path):
                print(f"Skipping invalid cape (must be 2:1 width:height): {cape_path}")
                continue
            with open(cape_path, "rb") as f:
                cape_png = f.read()

            skin_id = _unique_skin_id(used_ids, rng)
            entries.append((skin_id, _skin_display_name(cape_path),
                            skin_png, cape_png, anim_flags))
    else:
        for skin_file in _iter_skin_files(skins_folder):
            with open(skin_file, "rb") as f:
                skin_png = f.read()
            skin_id = _unique_skin_id(used_ids, rng)
            entries.append((skin_id, _skin_display_name(skin_file),
                            skin_png, None, default_anim_flags(skin_file)))

    for skin_id, display_name, skin_png, cape_png, anim_flags in entries:
        assets.append(build_skin_asset(skin_png, display_name, skin_id,
                                       has_cape=cape_png is not None,
                                       anim_flags=anim_flags))
        if cape_png is not None:
            assets.append(build_cape_asset(cape_png, skin_id))

    loc_asset = next((a for a in assets
                      if a.type == ASSET_LOCALISATION), None)
    if loc_asset is not None and entries:
        loc = parse_loc_file(loc_asset.data)
        if not loc.has_uids:
            add_loc_entries(loc, {
                f"IDS_dlcskin{skin_id:08d}_DISPLAYNAME": display_name
                for skin_id, display_name, _, _, _ in entries
            })
            loc_asset.data = write_loc_file(loc)

    write_pck(assets, output_path, little_endian=pck.little_endian)
    return output_path


def _set_param(asset, key, value):
    for i, (k, _) in enumerate(asset.params):
        if k == key:
            asset.params[i] = (key, value)
            return
    asset.params.append((key, value))


def _remove_param(asset, key):
    asset.params[:] = [p for p in asset.params if p[0] != key]


def _find_asset(assets, filename):
    return next((a for a in assets if a.filename == filename), None)


def _remove_loc_keys(assets, keys_to_remove):
    loc_asset = next((a for a in assets if a.type == ASSET_LOCALISATION), None)
    if loc_asset is None:
        return
    loc = parse_loc_file(loc_asset.data)
    if loc.has_uids:
        return
    for key in keys_to_remove:
        loc.keys.pop(key, None)
    loc_asset.data = write_loc_file(loc)


def edit_skin_pack(pck_path, skin_index, operation, file_path=None, new_name=None):
    pck = read_pck(pck_path)
    skins = pck.get_skins()
    skin = skins[skin_index]
    asset = skin["asset"]
    skin_id = skin["id"]

    if operation == "1":
        with open(file_path, "rb") as f:
            asset.data = f.read()
        _set_param(asset, "ANIM", f"0x{default_anim_flags(file_path):08x}")

    elif operation == "2":
        if not is_valid_cape(file_path):
            raise ValueError("Cape image must be twice as wide as it is tall (e.g. 64x32).")
        with open(file_path, "rb") as f:
            cape_png = f.read()

        capepath = asset.get_param("CAPEPATH")
        cape_asset = _find_asset(pck.assets, capepath) if capepath else None
        if cape_asset is not None:
            cape_asset.data = cape_png
        else:
            cape_asset = build_cape_asset(cape_png, skin_id)
            pck.assets.append(cape_asset)
            _set_param(asset, "CAPEPATH", cape_asset.filename)

    elif operation == "3":
        capepath = asset.get_param("CAPEPATH")
        _remove_param(asset, "CAPEPATH")
        if capepath:
            cape_asset = _find_asset(pck.assets, capepath)
            if cape_asset is not None:
                pck.assets.remove(cape_asset)

    elif operation == "4":
        capepath = asset.get_param("CAPEPATH")
        pck.assets.remove(asset)
        if capepath:
            cape_asset = _find_asset(pck.assets, capepath)
            if cape_asset is not None:
                pck.assets.remove(cape_asset)
        _remove_loc_keys(pck.assets, [
            f"IDS_dlcskin{skin_id:08d}_DISPLAYNAME",
            f"IDS_dlcskin{skin_id:08d}_THEMENAME",
        ])

    elif operation == "5":
        _set_param(asset, "DISPLAYNAME", new_name)

        loc_asset = next((a for a in pck.assets if a.type == ASSET_LOCALISATION), None)
        if loc_asset is not None:
            loc = parse_loc_file(loc_asset.data)
            if not loc.has_uids:
                set_loc_entries(loc, {
                    f"IDS_dlcskin{skin_id:08d}_DISPLAYNAME": new_name,
                })
                loc_asset.data = write_loc_file(loc)

    write_pck(pck.assets, pck_path, little_endian=pck.little_endian)
    return pck_path


def handle_append(answers):
    output_path = add_to_pack(
        answers["pck_path"],
        answers["pck_path"],
        answers["add_mode"],
        skin_path=answers.get("skin_path"),
        skins_folder=answers.get("skins_folder"),
        capes_folder=answers.get("capes_folder"),
    )
    print(f"Pack updated: {output_path}")


def handle_edit_skin(answers):
    pck = read_pck(answers["pck_path"])
    skins = pck.get_skins()
    if not skins:
        print("No skins found in that pack.")
        return
    edit = ask_skin_edit(skins)
    edit_skin_pack(answers["pck_path"], **edit)
    print(f"Pack updated: {answers['pck_path']}")
