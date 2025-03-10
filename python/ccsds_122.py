from PIL import Image
import numpy as np
import struct

import discrete_wavelet_transform as dwt
import bitplane_encoder as bpe
import file_io
import run_length_encoding as rle
from subband_scaling import scale, rescale
from common import pad_data_to_8

import os, sys
sys.path.append(os.path.abspath('./cython'))
import c_dwt as c_dwt

def compress_data(data, width, height, bitdepth=8):

    data, pad_width, pad_height = pad_data_to_8(data, width, height)
    width += pad_width
    height += pad_height

    #Do DWT in Cython
    num_pixels = width*height
    c_data = np.zeros(num_pixels, dtype='int32')
    for i in range(height):
        for j in range(width):
            c_data[i * width + j] = data[i][j]
    c_data = struct.pack(f'{num_pixels}I', *c_data)

    levels = 3
    c_dwt.c_discrete_wavelet_transform_2D(c_data, width, height, levels, False)

    c_data = np.array(struct.unpack(f'{num_pixels}i', c_data)).astype('int32')
    for i in range(height):
        for j in range(width):
            data[i][j] = c_data[i * width + j]
    #end Cython DWT

    scale(data, width, height)

    file_io.fp = open("output.cmp", "wb")
    bpe.encode(data, width, height, pad_width, bitdepth)
    file_io.cleanup()


def compress(filein="../res/noise/test_image_noise_32.bmp", fileout='output'):

    # Load from file and initialize data to correct dimensions
    data, width, height = file_io.load_image(filein)
    data, pad_width, pad_height = pad_data_to_8(data, width, height)
    width += pad_width
    height += pad_height
    data = data.astype('int32')

    data_in = np.copy(data)

    #Do DWT in Cython
    num_pixels = width*height
    c_data = np.zeros(num_pixels, dtype='int32')
    for i in range(height):
        for j in range(width):
            c_data[i * width + j] = data[i][j]
    c_data = struct.pack(f'{num_pixels}I', *c_data)

    levels = 3
    c_dwt.c_discrete_wavelet_transform_2D(c_data, width, height, levels, False)

    c_data = np.array(struct.unpack(f'{num_pixels}i', c_data)).astype('int32')
    for i in range(height):
        for j in range(width):
            data[i][j] = c_data[i * width + j]
    #end Cython DWT

    scale(data, width, height)

    file_io.fp = open(fileout+".cmp", "wb")
    bitdepth = 8
    bpe.encode(data, width, height, pad_width, bitdepth)
    file_io.cleanup()

    return data_in, width, height, bitdepth

    """
    #NOTE: Run length encoding is currently a separate prosess
    #In the future data should be piped through during bitplane encoding

    fp = open(fileout+".cmp", 'rb')
    temp = fp.read()
    fp.close()
    temp = rle.compress(temp)
    new_size = int(len(temp)/8)

    fp = open(fileout+".cmp", 'wb')
    fp.write(int(temp, 2).to_bytes(new_size, 'big'))
    fp.close()
    """


if __name__ == '__main__':
    compress()
