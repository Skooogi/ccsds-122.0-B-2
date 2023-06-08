from PIL import Image
import numpy as np
import math
import os

import dwt
import ccsds

def test_DWT() -> None:
    
    bitdepth = 8

    filein = "res/png/7.png"
    fileout = "test_output.png"
    
    img_in = Image.open(filein)
    data_a = np.array(img_in.split()[0], dtype=int)
    width, height = img_in.size
    img_in.close()

    data_b = np.copy(data_a)

    data_a, pad_width, pad_height = ccsds.pad_image_size(data_a, width, height)
    width += pad_width
    height += pad_height

    levels = 3
    dwt.discrete_wavelet_transform_2D(data_a, width, height, levels)
    dwt.discrete_wavelet_transform_2D(data_a, width, height, levels, True)

    #Remove padding
    data_a = data_a[:height-pad_height,:width-pad_width]

    a_height, a_width = np.shape(data_a)
    b_height, b_width = np.shape(data_b)

    assert a_height == b_height
    assert a_width == b_width

    n = a_height * a_width
    
    #MSE
    mean_squared_error = 0
    for i in range(a_height):
        for j in range(a_width):
            temp = data_b[i,j] - data_a[i,j] 
            temp = temp * temp
            mean_squared_error += temp

    mean_squared_error /= n

    #PSNR
    peak_signal_to_noise_ratio = math.inf
    if(mean_squared_error != 0):
        peak_signal_to_noise_ratio = 10*math.log((255*255)/mean_squared_error, 10)

    print("PSNR", peak_signal_to_noise_ratio)
    assert peak_signal_to_noise_ratio > 40
