import numpy as np

import file_io
import ccsds_122 as comp
import rccsds_122 as decomp

from random import randint, seed

from common import MSE, PSNR

def testFile(fileName):
    print("Testing ",fileName)
    data_in, width, height, bitdepth = comp.compress(fileName)
    data_out = decomp.decompress()
    
    mean_squared_error = MSE(data_in, data_out, width, height)
    if mean_squared_error == 0:
        print("Final result: Success.")
    else:
        print("Final result: ERROR. ERROR. ERROR. ERROR. ERROR. ERROR. ERROR. ERROR.")
        print(f'MSE: {mean_squared_error}, PSNR: {PSNR(mean_squared_error, bitdepth)} dB')
        print("Stopping!")
        exit(1)

def testData(data, width, height, bitdepth):

    data_in = np.copy(data)
    #NOTE compress_data() mutates data
    comp.compress_data(data, width, height, bitdepth)
    decompressed_data = decomp.decompress()

    mean_squared_error = MSE(data_in, decompressed_data, width, height)
    if mean_squared_error == 0:
        print("Final result: Success.")
    else:
        print("Final result: ERROR. ERROR. ERROR. ERROR. ERROR. ERROR. ERROR. ERROR.")
        print(f'MSE: {mean_squared_error}, PSNR: {PSNR(mean_squared_error, bitdepth)} dB')
        print("Stopping!")
        exit(1)

def randomtests():

    # ------------------------------------------------------------------------------
    # Parameters of the test:
    # ------------------------------------------------------------------------------

    # The total number of random images to test
    num_images = 30

    # The minimum and maximum image width. Note that the image width must be a multiple 
    # of eight (8), if we want to avoid the use of padding!
    min_width = 32
    max_width = 256

    # The minimum and maximum image height. Note that the image height must be a multiple 
    # of eight (8), if we want to avoid the use of padding!
    min_height = 32
    max_height = 256

    # The minimum and maximum bitdepth to use. (Currently only 8 bits supported by the code.)
    min_bitdepth = 1
    max_bitdepth = 15

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
        orig_img = np.random.randint(min_pixval, max_pixval + 1, (img_height, img_width))
        # print(orig_img)

        # Save the original input file.
        fname = "temp_orig_" + str(img_ind + 1) + ".bmp"
        testData(orig_img, img_width, img_height, img_bitdepth)

        """
        # Temporary file name
        fname = "temp_orig_" + str(img_ind + 1) + ".bmp"

        # Save the original input file.
        file_io.save_image(fname, orig_img, img_width, img_height)

        # Run the analysis
        testFile(fname)
        """

if __name__ == '__main__':

    test_case = 2

    # Checking compression + decompression of the test images supplied by Kasper:
    if test_case == 1:
        testFile("test/test_image_0.bmp")               # works!
        #testFile("test/test_image_1.bmp")             # works!
        #testFile("test/test_image_2.bmp")             # works!
        #testFile("test/test_image_3.bmp")             # NO PROBLEM! output is IDENTICAL to input. 
        #testFile("test/test_image_4.bmp")             # works!
        #testFile("test/test_image_gradient.bmp")      # works!

    if test_case == 2:
        randomtests()
    



