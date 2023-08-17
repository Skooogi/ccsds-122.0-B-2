import numpy as np
import os, sys
sys.path.append(os.path.abspath('../python'))
import ccsds_122 as comp
import rccsds_122 as decomp
import file_io
from common import MSE, PSNR, pad_data_to_8
from test_files import *

def check_decompressed_data(data_in, width, height, bitdepth):
    decompressed_data = decomp.decompress()
    mean_squared_error = MSE(data_in, decompressed_data, width, height)
    if mean_squared_error == 0:
        print(f'Final result: {bcolors.OKGREEN}Success{bcolors.ENDC}.')
    else:
        print(f'Final result: {bcolors.FAIL}ERROR. ERROR. ERROR. ERROR. ERROR. ERROR. ERROR. ERROR{bcolors.ENDC}.')
        print(f'MSE: {mean_squared_error}, PSNR: {PSNR(mean_squared_error, bitdepth)} dB')
        print("Stopping!")
        exit()

def test_data(data, width, height, bitdepth, check_python=1):

    data_in = np.copy(data)

    check_decompressed_data(data_in, width, height, bitdepth)

    #NOTE compress_data() mutates data
    if(check_python):
        print("Python")
        comp.compress_data(data, width, height, bitdepth)
        check_decompressed_data(data_in, width, height, bitdepth)

def test_images():

    for i,file in enumerate(raw_images):
        print('Testing image ' + file[0])
        print('  Width    = ' + str(file[1]))
        print('  Height   = ' + str(file[2]))
        print('  Bitdepth = ' + str(file[3]))
        print("C:")
        os.system(f'time ../build/ccsds.bin {file[0]} {"output.cmp"} {file[1]} {file[2]} {file[3]}')

        data, width, height = file_io.load_image(bmp_images[i])
        data_in, pad_width, pad_height = pad_data_to_8(data, width, height)
        width += pad_width
        height += pad_height
        check_python = 0
        print("Uncompressing")
        test_data(data_in, width, height, 8, check_python)
        print("*"*20)

if __name__ == "__main__":
    test_images()
