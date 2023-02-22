from PIL import Image
import numpy as np

import dwt
import tests

def bitplane_encoder(data, width, height):
    v = 1

if __name__ == '__main__':
    print("***DWT example***")
    img = Image.open('7.png')
    data = np.array(img.split()[0], dtype='float')
    reference = np.copy(data)
    img.close()

    #Padding
    width, height = img.size
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

    levels = 1
    for i in range(levels):
        print("DWT level",i+1)
        dwt.forward_DWT(data, width/(pow(2,i)), height/(pow(2,i)))

    p = 1000
    l = -1000
    for i in range(int(height)):
        for j in range(int(width)):
            if(i < height/2 and j < width/2):
                continue
            v = data[int(i),int(j)]
            if v > l:
                l = v
            if v < p:
                p = v

    print(l,p)

    for i in range(int(height)):
        for j in range(int(width)):
            if(i < height/2 and j < width/2):
                continue
            v = data[i,j]
            data[i, j] = ((v-p)/(l-p))*255

    #for i in reversed(range(levels)):
    #    print("IDWT level",i+1)
    #    dwt.backward_DWT(data, width/(pow(2,i)), height/(pow(2,i)))

    bitplane_encoder(data, width, height)

    print("Deleting padded rows and columns")
    data = data[:height-pad_height,:width-pad_width]

    img_out = Image.fromarray(data.astype('uint8'))
    img_out.save("output.png", format="PNG")
    img_out.close()

    #Sanity checks
    tests.MSE(data, reference)
    tests.PSNR(data, reference)
