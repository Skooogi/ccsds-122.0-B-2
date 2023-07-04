import numpy as np
import struct
from timeit import default_timer as timer

import file_io
import discrete_wavelet_transform as dwt
from common import MSE, PSNR, pad_data_to_8

import os
import cython.c_dwt as c_dwt


# Before testing comment out @njit decorators in discrete_wavelet_transform.py
# Otherwise njit implementation sometimes runs better as it doesn't have
# extra overhead from linkin C and python like cython does
def test_file(filename='test/test_image_2.bmp', bitdepth=8):

    data, width, height = file_io.load_image(filename)
    data, pad_width, pad_height = pad_data_to_8(data, width, height)
    width += pad_width
    height += pad_height

    num_pixels = width*height
    data = data.astype(np.int32)
    c_data = data.tobytes()

    levels = 3
    # Normal dwt
    start = timer()
    dwt.discrete_wavelet_transform_2D(data, width, height, levels)
    dwt.discrete_wavelet_transform_2D(data, width, height, levels, True)
    end = timer()
    print(f'DWT:\t{(end-start)*1000:.4f} ms')
    file_io.save_image("img_in.bmp", data, width, height)

    # C dwt
    start = timer()
    c_dwt.c_discrete_wavelet_transform_2D(c_data, width, height, levels, 0)
    c_dwt.c_discrete_wavelet_transform_2D(c_data, width, height, levels, 1)
    end = timer()
    print(f'C DWT:\t{(end-start)*1000:.4f} ms')
    print()

    c_data = np.frombuffer(c_data, dtype=np.int32).reshape(height, width)
    data_out = c_data.astype('uint8')

    file_io.save_image("img_out.bmp", data_out, width, height)
    mse = MSE(data_out, data, width, height)
    if (mse != 0):
        psnr = PSNR(mse, bitdepth)



if __name__ == '__main__':
    print("Tests speed difference between python and cython implementation of DWT")
    print("Timed process is 3 layers of transform followed by 3 levels of inverse transform")

    print("Compiling latest C source")
    os.system("(cd ./cython; python3 c_dwt_compile.py build_ext --inplace)")

    test_file("test/test_image_0.bmp")
    test_file("test/test_image_1.bmp")
    test_file("test/test_image_2.bmp")
    test_file("test/test_image_3.bmp")
    test_file("test/test_image_4.bmp")
    test_file("test/test_image_5.bmp")
