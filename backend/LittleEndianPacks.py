
# - PS Vita, PS4, Xbox One, Nintendo Switch have special pck packs. This scripts handles that

from .NormalPacks import build_skin_pack, write_pck, PckAsset


def write_pck_little_endian(assets, output_path):
    return write_pck(assets, output_path, little_endian=True)


def build_little_endian_skin_pack(skin_path, capes_folder, output_path,
                                  pack_name=None, pack_id=None, seed=None):
    return build_skin_pack(
        skin_path, capes_folder, output_path,
        pack_name=pack_name, pack_id=pack_id, seed=seed,
        little_endian=True,
    )
