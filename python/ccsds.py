from PIL import Image
import numpy as np

import dwt
import tests
import bpe
import subband
import rle

if __name__ == '__main__':
    print("***DWT example***")
    #img = Image.open('7.png')
    #data = np.array(img.split()[0], dtype='int')
    sizes = (604, 786)
    data = np.fromfile("7.raw", dtype=np.uint8).reshape(sizes).astype('int')
    #sizes = (1024,1024)
    #data = np.fromfile("raw_picture_12_0.raw", dtype=np.uint8).reshape(sizes).astype('int')
    reference = np.copy(data)
    #img.close()

    #Padding
    #width, height = img.size
    height, width = sizes
    pad_width = 8 - width % 8
    pad_height = 8 - height % 8
    if pad_width > 0 or pad_height > 0:
        print("Padding image to achieve side lengths that are multiples of 8")

        #Columns
        last_column = data[:,width - 1]
        last_column = last_column.reshape(height, 1)
        for i in range(pad_width):
            data = np.hstack((data, last_column))
        width = width + pad_width

        #Rows
        last_row = data[height - 1, :]
        last_row = last_row.reshape(1, width)
        for i in range(pad_height):
            data = np.vstack((data, last_row))
        height = height + pad_height

    
    levels = 3
    for i in range(levels):
        print("DWT level",i+1)
        dwt.forward_DWT(data, width/(pow(2,i)), height/(pow(2,i)))

    data = subband.scale(data, width, height)

    bpe.encode(data, width, height)
    print("Huffman coding")
    rle.compress("output.cmp")

    for i in reversed(range(levels)):
        print("IDWT level",i+1)
        dwt.backward_DWT(data, width/(pow(2,i)), height/(pow(2,i)))
    
    """
    for i in range(int(height/8)):
        for j in range(int(width/8)):
            data[i][j] = 255
    """ 
    
    print("Deleting padded rows and columns")
    data = data[:height-pad_height,:width-pad_width]

    img_out = Image.fromarray(data.astype('uint8'))
    img_out.save("output.png", format="PNG")
    img_out.close()

    #Sanity checks
    #tests.MSE(data, reference)
    #tests.PSNR(data, reference)
