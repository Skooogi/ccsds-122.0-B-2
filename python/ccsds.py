from PIL import Image
import numpy as np

import dwt
import bpe
import subband
import rle


#Pad image width and height to multiples of 8
def pad_image_size(data, width, height):

    pad_width = 8 - width % 8
    pad_height = 8 - height % 8

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

def compress(filein, fileout):

    img = Image.open(filein)
    data = np.array(img.split()[0], dtype='int')
    width, height = img.size
    img.close()
    #sizes = (604, 786)
    #data = np.fromfile("7.raw", dtype=np.uint8).reshape(sizes).astype('int')

    data, pad_width, pad_height = pad_image_size(data, width, height)
    width += pad_width
    height += pad_height

    levels = 1

    dwt.discrete_wavelet_transform_2D(data, width, height, levels)
    #subband.scale(data, width, height)

    #TODO Remove below this line
    #subband.rescale(data, width, height)
    dwt.discrete_wavelet_transform_2D(data, width, height, levels, True)

    #Remove padding
    data = data[:height-pad_height,:width-pad_width]
    img_out = Image.fromarray(data.astype('uint8'))
    img_out.save(fileout, format="PNG")
    img_out.close()

if __name__ == '__main__':
    compress("res/png/7.png", "output.png")
