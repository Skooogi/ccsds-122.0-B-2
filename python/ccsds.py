from PIL import Image
import numpy as np

import discrete_wavelet_transform as dwt
import bitplane_encoder as bpe
import run_length_encoding as rle
from file_io import load_image, save_image
from subband_scaling import scale, rescale

#Pad image width and height to multiples of 8
def pad_image_size(data, width, height):

    pad_width = 8 - width % 8
    pad_height = 8 - height % 8

    pad_width = 0 if pad_width == 8 else pad_width
    pad_height = 0 if pad_height == 8 else pad_height

    if 0 < pad_width < 8:
        last_column = data[:,width - 1]
        last_column = last_column.reshape(height, 1)
        for i in range(pad_width):
            data = np.hstack((data, last_column))

    if 0 < pad_height < 8:
        last_row = data[height - 1, :]
        last_row = last_row.reshape(1, width+pad_width)
        for i in range(pad_height):
            data = np.vstack((data, last_row))

    return data, pad_width, pad_height

def compress(filein="test/test_image_0.bmp", fileout='output.bmp'):

    data, width, height = load_image(filein)
    data, pad_width, pad_height = pad_image_size(data, width, height)
    width += pad_width
    height += pad_height

    levels = 3

    print("DWT")
    dwt.discrete_wavelet_transform_2D(data, width, height, levels)
    print("Scaling")
    scale(data, width, height)

    print("Bitplane encoding")
    bpe.encode(data, width, height, pad_width)

    """
    print("Run length encoding")
    fp = open("output.cmp", 'rb')  
    temp = fp.read()
    fp.close()
    temp = rle.compress(temp)
    new_size = int(len(temp)/8)
    print(new_size/len(temp))
    fp = open("output.cmp", 'wb')  
    fp.write(int(temp, 2).to_bytes(new_size, 'big'))
    fp.close()

    print("Run length decoding")
    fp = open("output.cmp", 'rb')  
    temp = fp.read()
    fp.close()
    temp = rle.uncompress(temp)
    new_size = int(len(temp)/8)
    print(new_size/len(temp))
    fp = open("output.cmp", 'wb')  
    for byte in temp:
        fp.write(int(byte).to_bytes(1, 'big'))
    fp.close()
    """

    #TODO Remove below this line
    print("Rescaling")
    rescale(data, width, height)
    print("IDWT")
    dwt.discrete_wavelet_transform_2D(data, width, height, levels, True)

    #Remove padding
    data = data[:height-pad_height,:width-pad_width]
    save_image(fileout, data, width, height)

if __name__ == '__main__':
    compress()
