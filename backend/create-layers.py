import pathlib
import os

LAYERS_DIR = "./layers/main_layer/python/lib/python3.11/site-packages"
pathlib.Path(LAYERS_DIR).mkdir(parents = True, exist_ok = True)

os.system(f"pip3 install -r requirements.txt --target {LAYERS_DIR}")