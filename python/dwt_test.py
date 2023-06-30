import ccsds_122 as comp
import rccsds_122 as decomp

import numpy as np
import struct
from timeit import default_timer as timer

import file_io
import discrete_wavelet_transform as dwt
from common import MSE, PSNR, pad_data_to_8

import cython.c_dwt as c_dwt

def test_file(filename = 'test/test_image_2.bmp', bitdepth = 8):

    data, width, height = file_io.load_image(filename)
    data, pad_width, pad_height = pad_data_to_8(data, width, height)
    width += pad_width
    height += pad_height

    num_pixels = width*height
    c_data = np.zeros(num_pixels, dtype=np.int32)
    for i in range(height):
        for j in range(width):
            c_data[i * width + j] = data[i][j]
    c_data = struct.pack(f'{num_pixels}I', *c_data)

    levels = 3
    #Normal dwt
    start = timer()
    dwt.discrete_wavelet_transform_2D(data, width, height, levels)
    dwt.discrete_wavelet_transform_2D(data, width, height, levels, True)
    end = timer()
    print(f'DWT: {(end-start)*1000:.4f} ms')
    file_io.save_image("img_in.bmp", data, width, height)

    #C dwt
    start = timer()
    c_data = c_dwt.c_discrete_wavelet_transform_2D(c_data, width, height, levels, 0)
    c_data = c_dwt.c_discrete_wavelet_transform_2D(c_data, width, height, levels, 1)
    end = timer()
    print(f'C DWT: {(end-start)*1000:.4f} ms')

    c_data = struct.unpack(f'{num_pixels}I', c_data)
    for i in range(height):
        for j in range(width):
            data[i][j] = c_data[i * width + j]
    file_io.save_image("img_out.bmp", data, width, height)

if __name__ == '__main__':

    test_file()
