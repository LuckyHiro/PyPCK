import os


def _clean_path(text):
    return text.strip().strip("\"'")


def _print_banner():
    art_path = os.path.join(os.path.dirname(__file__), "Art.txt")
    if os.path.exists(art_path):
        with open(art_path, "r", encoding="utf-8") as f:
            print(f.read())


def ask_questions():
    _print_banner()
    print("PyPCK v1.0:")
    print("- 1: Make Easy Cape Pack")
    print("- 2: Make Easy Skin Pack")
    print("- 3: Extract From PCKs")
    print("- 4: Add Onto Existing Pack")
    print("- 5: Add Onto Existing Pack (Capes)")
    print("- 6: Edit Skin Pack")
    pack_type = input("Enter an option: ").strip()

    if pack_type == "3":
        pck_path = _clean_path(input("Enter the path to the .pck file: "))

        print("Extract Options:")
        print("- 1: Extract Everything")
        print("- 2: Pick Whats Extracted")
        extract_mode = input("Enter an option: ").strip()

        if extract_mode == "1":
            extract_dir = _clean_path(input("Enter the folder to extract into: "))
            return {
                "type": "extract",
                "extract_mode": "1",
                "pck_path": pck_path,
                "extract_dir": extract_dir,
            }
        return {
            "type": "extract",
            "extract_mode": "2",
            "pck_path": pck_path,
        }

    if pack_type in ("4", "5"):
        pck_path = _clean_path(input("Enter the path to the existing .pck file: "))

        result = {
            "type": "append" if pack_type == "4" else "append_capes",
            "pck_path": pck_path,
        }

        if pack_type == "5":
            result["add_mode"] = "1"
            result["skin_path"] = _clean_path(input("Enter the path to the skin image: "))
            result["capes_folder"] = _clean_path(input("Enter the path to the folder containing cape images: "))
            return result

        result["add_mode"] = "2"
        result["skins_folder"] = _clean_path(input("Enter the path to the folder containing skin images: "))
        return result

    if pack_type == "6":
        pck_path = _clean_path(input("Enter the path to the existing .pck file: "))
        return {
            "type": "edit_skin_pack",
            "pck_path": pck_path,
        }

    skin_path = _clean_path(input("Enter the path to the skin image: "))

    capes_folder = None
    if pack_type == "1":
        capes_folder = _clean_path(input("Enter the path to the folder containing cape images: "))

    output_path = _clean_path(input("Enter the path for the output .pck file: "))

    print("What Platform Is The Pack For?")
    print("- 1: Windows64, Xbox 360, Wii U, PS3")
    print("- 2: PS Vita, PS4, Xbox One, Switch")
    platform = input("Enter the platform number: ").strip()

    return {
        "type": "cape_pack" if pack_type == "1" else "skin_pack",
        "skin_path": skin_path,
        "capes_folder": capes_folder,
        "output_path": output_path,
        "platform": platform,
    }
