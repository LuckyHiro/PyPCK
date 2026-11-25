# PyPCK
A python CLI based program to create and edit Minecraft legacy skin packs easily


# Features

- Quick Make Skin packs with a single skin, and a folder of capes

- Quick Make Skin packs using a folder of skins

- Addon to already existing skin packs in mass using folders of skins/capes

- Extract Assets/Info from packs

- Edit Existing Skin Packs

- IDs are auto generated

- Names are auto made based on the skin/cape file name.

_________________________________________________________________________________
# Important Info

> **PyPCK will ask which platform the pack is being made for, as there are two types of pck pack formats for legacy console. Each console is listed out fully in PyPCK, but they are placed in groups that may seem odd at first.**
> 
> - **Normal PCK Packs:** Windows64 Leak, Xbox 360, PS3, Wii U, 3Ds. This is the "default"/first version of pck packs.
> 
> - **Special PCK Packs:** PS Vita, Xbox One, PS4, & Switch. This is the newer version of pck packs

> The program is heavily based on PCKStudio. I just wanted a faster version that automated large chunks of it.

_________________________________________________________________________________
## Project Layout

|_ pypck.py (Program Launch Script

|_ /Backend

   |_ Questions.py (Handles the questions)
  
   |_ PCKReader.py (Handles Reading PCK Packs)
  
   |_ ExtractPacks.py (Handles Extracting Packs)
  
   |_ EditPacks.py (Handles Editing Packs)
  
   |_ LOCFile.py (Handles LoC part of adding skins)
  
   |_ NormalPacks.py (Handles comp for normal packs)
  
   |_ LittleEndianPacks.py (Handles comp for the special/newer packs)
   
   |_ Art.txt (Program Banner)
   
   |_ __init__.py (allows for the backend folder so the root isn't a mess)



