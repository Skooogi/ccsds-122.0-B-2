from PIL import Image
import numpy as np

def forward_DWT(data, width, height):

    #Horizontal
    for i in range(int(height)):

        cache = np.copy(data[i, :int(width)])

        #The first index is an exception and is calculated separately
        x0 = cache[0]
        x1 = cache[1]
        x2 = cache[2]
        x4 = cache[4]
        highpass = x1 -( 9/16 * (x0 + x2) - 1/16 * (x2 + x4) + 1/2 )
        data[i, int(width / 2)] = highpass

        lowpass = x0 - ( -highpass/2 + 1/2 )
        data[i, 0] = lowpass

        for j in range(1, int(width/2) - 2):

            x0 = cache[2*j]
            x1 = cache[2*j+1]
            x2 = cache[2*j+2]
            x_2 = cache[2*j-2]
            x4 = cache[2*j+4]

            highpass = x1 -( 9/16 * (x0 + x2) - 1/16 * (x_2 + x4) + 1/2 )
            data[i, int(j + width/2)] = highpass

            lowpass = x0 - ( -(data[i, int(j-1 + width/2)]+highpass)/4 + 1/2 )
            data[i, int(j)] = lowpass

        
        #N-2
        x0 = cache[int(width) - 2]
        x_1 = cache[int(width) - 3]
        x_2 = cache[int(width) - 4]
        x_4 = cache[int(width) - 6]
        highpass = x_1 - ( 9/16 * (x_2 + x0) - 1/16 * (x_4 + x0) + 1/2 )
        data[i, int(width)-2] = highpass
        lowpass = x0 - ( -(data[i, int(width) - 3] + highpass)/4 + 1/2 )
        data[i, int(width/2)-1] = lowpass

        #N-1
        x0 = cache[int(width) - 1]
        x_1 = cache[int(width) - 2]
        x_3 = cache[int(width) - 4]
        highpass = x0 - ( 9/8 * x_1 - 1/8 * x_3 + 1/2 )
        data[i, int(width)-1] = highpass
        lowpass = x0 - ( -(data[i, int(width) - 2] + highpass)/4 + 1/2 )
        data[i, int(width/2)] = lowpass

    #Vertical
    for j in range(int(width)):

        cache = np.copy(data[:int(height), j])

        #The first index is an exception and is calculated separately
        x0 = cache[0]
        x1 = cache[1]
        x2 = cache[2]
        x4 = cache[4]
        highpass = x1 -( 9/16 * (x0 + x2) - 1/16 * (x2 + x4) + 1/2 )
        data[int(height/2), j] = highpass

        lowpass = x0 - ( -highpass/2 + 1/2 )
        data[0, j] = lowpass

        for i in range(1, int(height/2) - 2):

            x0 = cache[2*i]
            x1 = cache[2*i+1]
            x2 = cache[2*i+2]
            x_2 = cache[2*i-2]
            x4 = cache[2*i+4]

            highpass = x1 -( 9/16 * (x0 + x2) - 1/16 * (x_2 + x4) + 1/2 )
            data[int(i + height/2), j] = highpass

            lowpass = x0 - ( -(data[int(i-1 + height/2), j]+highpass)/4 + 1/2 )
            data[i, j] = lowpass

        #N-2
        x0 = cache[int(height) - 2]
        x_1 = cache[int(height) - 3]
        x_2 = cache[int(height) - 4]
        x_4 = cache[int(height) - 6]
        highpass = x_1 - ( 9/16 * (x_2 + x0) - 1/16 * (x_4 + x0) + 1/2 )
        data[int(height) - 2, j] = highpass
        lowpass = x0 - ( -(data[i, int(width) - 3] + highpass)/4 + 1/2 )
        data[int(height/2) - 1, j] = lowpass

        #N-1
        x0 = cache[int(height) - 1]
        x_1 = cache[int(height) - 2]
        x_3 = cache[int(height) - 4]
        highpass = x0 - ( 9/8 * x_1 - 1/8 * x_3 + 1/2 )
        data[int(height) - 1, j] = highpass
        lowpass = x0 - ( -(data[i, int(width) - 2] + highpass)/4 + 1/2 )
        data[int(height/2), j] = lowpass

if __name__ == '__main__':
    print("***DWT example***")
    img = Image.open('7.png')
    data = np.array(img.split()[0], dtype='int32')
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

    forward_DWT(data, width, height)
    forward_DWT(data, width/2, height/2)
    forward_DWT(data, width/4, height/4)

    img_out = Image.fromarray(data.astype('uint8'))
    img_out.save("output.png", format="PNG")
    #img_out.show()
