import os, sys
sys.path.append(os.path.abspath('../python'))
sys.path.append(os.path.abspath('../python/cython'))
from common import MSE, PSNR
from common_testing import *
from random import randint, seed
import ccsds_122 as comp
import file_io
import numpy as np
import rccsds_122 as decomp

def check_decompressed_data(data_in, width, height, bitdepth):
    decompressed_data = decomp.decompress()
    mean_squared_error = MSE(data_in, decompressed_data, width, height)
    if mean_squared_error == 0:
        print(f'Final result: {bcolors.OKGREEN}Success{bcolors.ENDC}.')
    else:
        print(f'Final result: {bcolors.FAIL}ERROR. ERROR. ERROR. ERROR. ERROR. ERROR. ERROR. ERROR{bcolors.ENDC}.')
        print(f'MSE: {mean_squared_error}, PSNR: {PSNR(mean_squared_error, bitdepth)} dB')
        print("Stopping!")
        exit()

def test_data(data, width, height, bitdepth, check_python=1):

    data_in = np.copy(data)

    check_decompressed_data(data_in, width, height, bitdepth)

    #NOTE compress_data() mutates data
    if(check_python):
        print("Python")
        comp.compress_data(data, width, height, bitdepth)
        check_decompressed_data(data_in, width, height, bitdepth)

def randomtests():

    # ------------------------------------------------------------------------------
    # Parameters of the test:
    # ------------------------------------------------------------------------------

    # The total number of random images to test
    num_images = 20

    # The minimum and maximum image width. Note that the image width must be a multiple 
    # of eight (8), if we want to avoid the use of padding!
    min_width = 32
    max_width = 2048

    # The minimum and maximum image height. Note that the image height must be a multiple 
    # of eight (8), if we want to avoid the use of padding!
    min_height = 32
    max_height = 2048

    # The minimum and maximum bitdepth to use. (Currently only bitdepths up to 14 supported)
    min_bitdepth = 1
    max_bitdepth = 16

    # The seed to use for the run. Arbitrary. Always setting the same seed so that the
    # results are reproducible.
    seed_value = 0

    # ------------------------------------------------------------------------------
    # Start the test:
    # ------------------------------------------------------------------------------

    # Set the seed. Any value ok here, just to make the following deterministic 
    # from run to run. Can change it to try different sets of images.
    seed(seed_value)
    np.random.seed(seed_value)

    # Test each image separately
    for img_ind in range(0,num_images):
        
        # Show progress
        print('Testing image ' + str(img_ind + 1) + ' of ' + str(num_images) + '.')

        # Randomly select image width/height which are multiples of 8
        while True:
            img_width = randint(min_width, max_width)
            if (img_width % 8) == 0:
                break

        while True:
            img_height = randint(min_height, max_height)
            if (img_height % 8) == 0:
                break
        
        # Randomly select the bit depth:
        img_bitdepth = randint(min_bitdepth, max_bitdepth)

        # Show what was chosen
        print('  Width    = ' + str(img_width))
        print('  Height   = ' + str(img_height))
        print('  Bitdepth = ' + str(img_bitdepth))

        # Calculate min and max pixel values
        min_pixval = 0
        max_pixval = (2**img_bitdepth)-1
        print('  Minval   = ' + str(min_pixval))
        print('  Maxval   = ' + str(max_pixval))

        # Create the actual image contents
        orig_img = np.random.randint(min_pixval, max_pixval + 1, (img_height, img_width), dtype='uint32')

        # Temporary file name
        fname_in = "temp_orig_" + str(img_ind + 1) + '.raw'
        fname_out = 'output.cmp'
        #Write file for c implementation to read
        orig_img.tofile(fname_in)

        #uncomment if you want to seegenerated images
        file_io.save_image(fname_in[:-4] + '.bmp', orig_img, img_width, img_height)

        print("C:")
        os.system(f'time ../build/ccsds.bin {fname_in} {fname_out} {img_width} {img_height} {img_bitdepth}')
        check_python = 0
        test_data(orig_img, img_width, img_height, img_bitdepth, check_python)
        print("*"*20)
        os.system(f'rm {fname_in} {fname_out} {fname_in[:-4]+".bmp"}')

if __name__ == '__main__':

    randomtests()
