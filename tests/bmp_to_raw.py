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
    root_folder = "../res"

    files = list(Path(root_folder).rglob("*.[bB][mM][pP]"))

    for filename in files:
        data, width, height = file_io.load_image(str(filename))

        #print(filename)
        data_out = np.zeros([width*height], dtype='int32')
        for i in range(height):
            for j in range(width):
                data_out[i*width+j] = data[i][j]

        out_filename = os.path.dirname(filename) + "/raw/" + (os.path.basename(filename)[:-3] + "raw")
        print(out_filename)
        data_out.tofile(out_filename)
