import file_io
import numpy as np
import os


if __name__ == '__main__':
    files = [
        "../res/noise/test_image_noise_32.bmp",
        "../res/noise/test_image_noise_64.bmp",
        "../res/noise/test_image_noise_128.bmp",
        "../res/noise/test_image_noise_256.bmp",
        "../res/noise/test_image_noise_512.bmp",
        "../res/noise/test_image_noise_1k.bmp",
        "../res/noise/test_image_noise_2k.bmp",
        "../res/noise/test_image_noise_4k.bmp"
    ]

    for filename in files:
        data, width, height = file_io.load_image(filename)

        print(filename)
        data_out = np.zeros([width*height], dtype='int32')
        for i in range(height):
            for j in range(width):
                data_out[i*width+j] = data[i][j]

        out_filename = (os.path.basename(filename)[:-3] + "raw")
        data_out.tofile(out_filename)