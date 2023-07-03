from file_io import load_image 
import numpy as np
import time

import run_length_encoding as rle

test_data_0 = load_image("test/test_image_0.bmp")[0]
test_data_1 = load_image("test/raw_picture_21_0.raw", 30, 1024)[0]
test_data_2 = load_image("test/raw_picture_19_0.raw", 30, 1024)[0]
test_data_3 = load_image("test/test_image_1.bmp")[0]
test_data_4 = load_image("test/raw_picture_12_0.raw", 1024, 1024)[0]
test_data_5 = load_image("test/raw_picture_11_0.raw", 2048, 2048)[0]
test_data_6 = load_image("test/test_image_2.bmp")[0]
test_data_7 = load_image("test/test_image_3.bmp")[0]
test_data_8 = load_image("test/test_image_4.bmp")[0]


def single_rle(data_in, test) -> None:

    data = np.copy(data_in.flatten())
    original_size = len(data)

    comp_start_time = time.time() 
    bitstring = rle.compress(data)
    comp_end_time = time.time() 

    new_size = int(len(bitstring) / 8)
    

    print("Test:",test)
    print("\torg:",f'\t{original_size} B')
    print("\tnew:",f'\t{new_size} B:')
    print("\tratio:",f'\t{(new_size/original_size):3.4f}')
    print("\tcomp:",f'\t{(comp_end_time-comp_start_time):3.4f} s')
    
    if(len(bitstring) % 8 != 0):
        print("DATA LENGHT % 8 != 0")
        exit(1)
    if(new_size >= original_size):
        print("Generated file not compressing data")
        exit(1)

    byt = int(bitstring, 2).to_bytes(new_size, 'big')
    comp_start_time = time.time() 
    result = rle.uncompress(byt)
    comp_end_time = time.time() 

    errors = 0
    for i in range(len(result)):
        errors += data[i] != result[i]
    if(errors):
        print("Process not lossless!")
        exit(1)

    print("\tucomp:",f'\t{(comp_end_time-comp_start_time):3.4f} s')

if __name__ == '__main__':
    single_rle(test_data_0, 0)
    single_rle(test_data_1, 1)
    single_rle(test_data_2, 2)
    single_rle(test_data_3, 3)
    single_rle(test_data_4, 4)
    single_rle(test_data_5, 5)
    single_rle(test_data_6, 6)
    single_rle(test_data_7, 7)
    print("This should fail from not compressing pure noise:")
    single_rle(test_data_8, 8)
