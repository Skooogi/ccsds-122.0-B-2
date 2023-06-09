import numpy as np
import math
import time
import os

import dwt
import ccsds
from file_io import load_image

test_data_0 = load_image("test/test_image_0.bmp")[0]
test_data_1 = load_image("test/raw_picture_21_0.raw", 30, 1024)[0]
test_data_2 = load_image("test/raw_picture_19_0.raw", 30, 1024)[0]
test_data_3 = load_image("test/test_image_1.bmp")[0]
test_data_4 = load_image("test/test_image_2.bmp")[0]
test_data_5 = load_image("test/raw_picture_12_0.raw", 1024, 1024)[0]
test_data_6 = load_image("test/raw_picture_11_0.raw", 2048, 2048)[0]

def test_dwt_0() -> None:
    single_dwt(test_data_0, 0)

def test_dwt_1() -> None:
    single_dwt(test_data_1, 1)

def test_dwt_2() -> None:
    single_dwt(test_data_2, 2)

def test_dwt_3() -> None:
    single_dwt(test_data_3, 3)

def test_dwt_4() -> None:
    single_dwt(test_data_4, 4)

def test_dwt_5() -> None:
    single_dwt(test_data_5, 5)

def single_dwt(data, test) -> None:

    data_b = np.copy(data)
    height, width = np.shape(data)

    data_a, pad_width, pad_height = ccsds.pad_image_size(data, width, height)
    width += pad_width
    height += pad_height

    levels = 3
    #Time transforms
    forward_start_time = time.time()
    dwt.discrete_wavelet_transform_2D(data_a, width, height, levels)
    forward_end_time = time.time()

    backward_start_time = time.time()
    dwt.discrete_wavelet_transform_2D(data_a, width, height, levels, True)
    backward_end_time = time.time()

    #Remove padding
    data_a = data_a[:height-pad_height,:width-pad_width]

    a_height, a_width = np.shape(data_a)
    b_height, b_width = np.shape(data_b)

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

    print("Test:", test)
    print("\tMSE", f'\t{mean_squared_error:3.4f}')
    print("\tPSNR", f'\t{peak_signal_to_noise_ratio:3.4f} dB')
    print("\tDWT", f'\t{(forward_end_time-forward_start_time):3.4f} s')
    print("\tIDWT", f'\t{(backward_end_time-backward_start_time):3.4f} s')
    
    assert peak_signal_to_noise_ratio == math.inf and mean_squared_error == 0
