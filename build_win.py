import os
import shutil

os.system("python -m PyInstaller --name ReCape --hiddenimport win32timezone --noconfirm main.py")

shutil.copytree("assets", "dist/ReCape/assets")
shutil.copyfile("layout.kv", "dist/ReCape/layout.kv")