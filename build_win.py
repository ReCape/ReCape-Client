import os
import shutil

os.system("python -m PyInstaller --name ReCape --hiddenimport win32timezone --noconfirm main.py")

try:
    shutil.copytree("assets", "dist/ReCape/assets")
except FileExistsError:
    pass

try:
    shutil.copyfile("layout.kv", "dist/ReCape/layout.kv")
except FileExistsError:
    pass