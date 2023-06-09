from PIL import Image
import numpy as np

def load_image(filein, raw_width = 0, raw_height = 0):
    
    if filein[-3:] == 'raw':
        data = np.fromfile(filein, dtype=np.uint8).reshape((raw_height, raw_width)).astype(int)
        return data, raw_width, raw_height

    img = Image.open(filein)
    data = np.array(img.split()[0], dtype='int')
    width, height = img.size
    img.close()

    return data, width, height

def save_data_to_image(fileout, data, width, height):

    img_out = Image.fromarray(data.astype('uint8'))
    img_out.save(fileout, format="PNG")
    img_out.close()

cache = 0
size = 0
def write_bits(data, bits):

    global cache, size

    for i in range(bits-1, -1, -1):
        cache <<= 1
        cache |= (data >> i) & 1
        size += 1

        if(size >= 8):
            fp.write(struct.pack('B',cache))
            cache = 0
            size = 0

def cleanup():
    global size
    if(size != 0):
        write.out(0, 8)

