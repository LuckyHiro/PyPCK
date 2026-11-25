from backend.Questions import ask_questions
from backend.NormalPacks import handle_new_pack
from backend.EditPacks import handle_append, handle_edit_skin
from backend.ExtractPacks import handle_extract

HANDLERS = {
    "cape_pack": handle_new_pack,
    "skin_pack": handle_new_pack,
    "append": handle_append,
    "append_capes": handle_append,
    "extract": handle_extract,
    "edit_skin_pack": handle_edit_skin,
}

answers = ask_questions()
HANDLERS[answers["type"]](answers)

# - lowkey, thought this project was gonna be way bigger, so I left 
# this script/the main script ultra thin, expecting to have to put more in there later.
#
# - I left it here to make it easy for people who may not know python, alongside
# keeping the cleaner folder layout.
#
# - but you can easily remove this and go straight to questions.py if you want.
