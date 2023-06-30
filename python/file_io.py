from PIL import Image
import numpy as np
import struct

def load_image(filein, raw_width = 0, raw_height = 0):
    
    #NOTE assumes 8 bits
    if filein[-3:] == 'raw':
        data = np.fromfile(filein, dtype=np.uint8).reshape((raw_height, raw_width)).astype(int)
        return data, raw_width, raw_height

    img = Image.open(filein)
    data = np.array(img.split()[0], dtype=np.int32)
    width, height = img.size
    img.close()

    return data, width, height

def save_image(fileout, data, width, height, img_format='BMP'):

    img_out = Image.fromarray(data.astype('uint8'))
    img_out.save(fileout, format=img_format)
    img_out.close()

fp = ''
cache = 0
size = 0
def out(data, bits): 
    
    #Packs given number of bits to bytes that are directly written to file
    #Left over bits are cached
    
    global size, cache

    for i in range(bits-1, -1, -1):
        cache <<= 1
        cache |= (data >> i) & 1
        size += 1

        if(size >= 8):
            fp.write(struct.pack('B',cache))
            cache = 0
            size = 0


def out_bits(data):

    #Helper for large bitstrings
    for i in range(len(data)):
        out(int(data[i]), 1)


def cleanup():
    #Writes any cached bits
    global size, fp
    if(size != 0):
        out(0, 8)
    fp.close()

    fp = ''
    size = 0
    cache = 0
