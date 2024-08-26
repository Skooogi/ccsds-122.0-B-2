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

def check_decompressed_data(data_comp, data_decomp, width, height, bitdepth):
    mean_squared_error = MSE(data_comp, data_decomp, width, height)
    if mean_squared_error == 0:
        print(f'Final result: {bcolors.OKGREEN}Success{bcolors.ENDC}.')
    else:
        print(f'Final result: {bcolors.FAIL}ERROR. ERROR. ERROR. ERROR. ERROR. ERROR. ERROR. ERROR{bcolors.ENDC}.')
        print(f'MSE: {mean_squared_error}, PSNR: {PSNR(mean_squared_error, bitdepth)} dB')
        print("Stopping!")
        exit()

def randomtests():

    #build ccsds
    os.system('make -C ..')
    #build cython library
    os.system('(cd ../python/cython; python3 c_dwt_compile.py build_ext --inplace)')

    nebraska_compressor = "nebraska.bin" #replace with decompressor location

    # ------------------------------------------------------------------------------
    # Parameters of the test:
    # ------------------------------------------------------------------------------

    # The total number of random images to test
    num_images = 1000

    # The minimum and maximum image width. Note that the image width must be a multiple 
    # of eight (8), if we want to avoid the use of padding!
    min_width = 32
    max_width = 1024

    # The minimum and maximum image height. Note that the image height must be a multiple 
    # of eight (8), if we want to avoid the use of padding!
    min_height = 32
    max_height = 1024

    # The minimum and maximum bitdepth to use. (Currently only bitdepths up to 12 supported)
    min_bitdepth = 1
    max_bitdepth = 12

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
        orig_img = np.random.randint(min_pixval, max_pixval + 1, (img_height, img_width), dtype='uint16')

        # Temporary file name
        fname_in = "temp_orig_" + str(img_ind + 1) + '.raw'
        fname_out = 'output.cmp'
        fname_decomp = fname_in[:-4] + '_decomp' + '.raw'
        #Write file for c implementation to read
        orig_img.tofile(fname_in)

        #uncomment if you want to see generated images
        file_io.save_image(fname_in[:-4] + '.bmp', orig_img, img_width, img_height)

        print("Compressing:")
        os.system(f'../build/ccsds.bin {fname_in} {fname_out} {img_width} {img_height} {img_bitdepth}')
        print("Decompressing:")
        os.system(f'time ./{nebraska_compressor} -b {img_bitdepth} -d {fname_out} -o {fname_decomp}')

        decomp_img = np.fromfile(fname_decomp, dtype=np.uint16 if img_bitdepth > 8 else np.uint8).reshape([img_height, img_width])
        #file_io.save_image(fname_decomp[:-4] + '.bmp', decomp_img, img_width, img_height)

        check_decompressed_data(orig_img.astype(np.int32), decomp_img.astype(np.int32), img_width, img_height, img_bitdepth)

        print("*"*20)
        os.system(f'rm {fname_decomp} {fname_decomp[:-4]+".bmp"} {fname_in} {fname_out} {fname_in[:-4]+".bmp"}')

if __name__ == '__main__':

    randomtests()
