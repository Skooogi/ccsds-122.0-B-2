import numpy as np
import os, sys
sys.path.append(os.path.abspath('../python'))
sys.path.append(os.path.abspath('../python/cython'))
import ccsds_122 as comp
import rccsds_122 as decomp
import file_io
from common import MSE, PSNR, pad_data_to_8
from test_files import *

def generate_strips(data, width, height, strip_height, num_strips, combinations): 

    file_out = "temp_strip_"
    print("Generating", num_strips, "strip images")
    images = []

    for i in range(num_strips):
        offset = np.random.randint(0, height-strip_height)
        cache = data[offset:offset+strip_height][:width]; 
        for j in range(1, combinations):
            offset = np.random.randint(0, height-strip_height)
            cache = np.append(cache, data[offset:offset+strip_height][:width]); 

        cache = cache.reshape(strip_height*combinations, width)
        cache.tofile(file_out + str(i+1) + '.raw')
        images += [["../tests/"+ file_out + str(i+1) + '.raw', width, strip_height*combinations, 8]]

    return images


def test_strips(images):

    file_out = 'output.cmp'

    ratio = 0

    for i,file in enumerate(images):
        #print('Testing image ' + file[0])
        #print("C:")
        os.system(f'../build/ccsds.bin {file[0]} {file_out} {file[1]} {file[2]} {file[3]} > /dev/null')
        file_compressed = os.path.getsize(file_out)
        file_size = file[1]*file[2]*file[3] // 8
        ratio += file_compressed/file_size 

        #print(file[0])
        os.system(f'rm {file[0]}')

    os.system(f'rm {file_out}')
    ratio /= len(images)

    with open("results.txt", "a") as f:
        print(ratio, file=f)

    if(ratio > 0.8):
        print(f'ratio: {bcolors.FAIL}{ratio:.3f}{bcolors.ENDC}')
    elif(ratio > 0.4):
        print(f'ratio: {bcolors.WARNING}{ratio:.3f}{bcolors.ENDC}')
    else:
        print(f'ratio: {bcolors.OKGREEN}{ratio:.3f}{bcolors.ENDC}')

if __name__ == "__main__":
    for img in bmp_images[-7:]:
        print("Strips generated from: ", img)
        data, width, height = file_io.load_image(img)
        images = generate_strips(data, int(width), int(height), 24, 100, 1)
        test_strips(images)
