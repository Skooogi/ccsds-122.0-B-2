import os,sys
sys.path.append(os.path.abspath('../python'))
import file_io
import numpy as np
from pathlib import Path

"""
Searches for all *.bmp files in root_folder recursively and
converts them to *.raw files
"""
if __name__ == '__main__':

    #Root folder for recursive search
    root_folder = "../res/opic/oraw"

    oraws = list(Path(root_folder).rglob("*.[oO][rR][aA][wW]"))
    metadata_paths = list(Path(root_folder).rglob("*.[tT][xX][tT]"))
    metadata = [os.path.dirname(x) + "/" + os.path.basename(x) for x in metadata_paths]

    noise = np.fromfile("../res/kohina_maski.raw", dtype=np.uint16).reshape(2048, 2048)

    for filename in oraws:

        file = os.path.basename(filename)
        file_data = [s for s in metadata if file in s][0]
        print(file, "->", file_data)

        width = 0
        height = 0
        #Read metadata to form image
        with open(file_data) as f:
            text = f.read().splitlines()
            sizes = [s for s in text if "window" in s]
            height = int(sizes[0].split(':')[1])
            width = int(sizes[1].split(':')[1])

        data = np.fromfile(filename, dtype=np.uint16)[:height*width].reshape(height, width)
        print(width, height, data)

        outfilename = "../res/opic/"+file[:-4] + "bmp"
        file_io.save_image(outfilename, data, width, height)
        if(width == 2048 and height == 2048):
            data = noise - data
            print("Removing noise")
        data.tofile("../res/opic/raw/"+file[:-4] + "raw")
