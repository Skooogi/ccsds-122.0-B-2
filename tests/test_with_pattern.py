import os, sys
sys.path.append(os.path.abspath('../python'))
from random import randint, seed
import numpy as np
import matplotlib.pyplot as plt
import array


def singletest():

    nebraska = "nebraska.bin"
    whitedwarf = "ccsds_122_0_b2_decoder"
    whitedwarf_format = 'u16le'

    # ------------------------------------------------------------------------------
    # Parameters of the test:
    # ------------------------------------------------------------------------------

    # The width and height of the image to be generated and used
    img_width = 2048
    img_height = 2048

    # The bitdepth of the image
    img_bitdepth = 10

    # The increment and mod when stepping along the x-axis (within a row)
    x_increment = 1
    x_mod = 16

    # The increment and mod when stepping along the y-axis (from row to row)
    y_mod = 16

    # The starting value (at position 0,0)
    start_value = 0

    # ------------------------------------------------------------------------------
    # Create the image:
    # ------------------------------------------------------------------------------

    # For simplicity first generating image like this, but will be overwritten below
    seed_value = 0
    seed(seed_value)
    np.random.seed(seed_value)
    orig_img = np.random.randint(0, 1, (img_height, img_width), dtype='uint16')

    # OK write the pattern.
    for y_pos in range(0,img_height):
        value = y_pos % y_mod
        for x_pos in range(0,img_width):
            orig_img[y_pos][x_pos] = value
            value += x_increment
            if (value == x_mod):
                value = 0

    min_value = 9999
    max_value = -1

    # Read the problematic file.
    problem_oraw_fname = "problem_opic_image.oraw"
    file_handle = open(problem_oraw_fname, "rb")
    byte_array = bytearray(file_handle.read())
    ind = 0
    y_pos = 0
    x_pos = 0
    first_byte = 0
    second_byte = 0
    for byte in byte_array:
        if ind >= 58:
            if ind & 1 == 0:
                first_byte = byte
            if ind & 1 == 1:
                second_byte = byte
                value = ((first_byte << 8) + second_byte) >> 6
                orig_img[y_pos][x_pos] = value
                if value > max_value:
                    max_value = value
                if value < min_value:
                    min_value = value
                x_pos += 1
                if (x_pos == 2048):
                    y_pos += 1
                    x_pos = 0
        ind += 1

    print(x_pos)
    print(y_pos)

    print(min_value)
    print(max_value)

    print(orig_img)

    # ------------------------------------------------------------------------------
    # Start the test:
    # ------------------------------------------------------------------------------

    # Temporary file names:

    # Set index to zero
    img_ind = 0

    # Input file ("raw" file, just the pixels, each pixel is represented as 2 bytes)
    fname_in = "temp_orig_" + str(img_ind + 1) + '.raw'

    # Compressed data file
    fname_out = 'output.cmp'

    # Decompressed image file
    fname_decomp = fname_in[:-4] + '_decomp' + '.raw'

    # Text version of compressed data
    fname_out_txt = 'output.cmp.txt'

    # OK, start the actual test:

    # Write the raw file for the c compression program implementation to read
    orig_img.tofile(fname_in)

    # Call the compressor program to compress the input image and produce the compressed file:
    print("Compressing:")
    print("CCSDS")
    os.system(f'cd .. && make && cd tests')
    cmd = f'../build/ccsds.bin {fname_in} {fname_out} {img_width} {img_height} {img_bitdepth}'
    os.system(cmd)
    #print("Nebraska")
    #os.system(f'time ./nebraska.bin -e {fname_in} -o {fname_out+".neb"} -w {img_width} -h {img_height} -b {img_bitdepth} -s 32')
    # print("Stopping as planned!")
    # exit()

    # Read the compressed data into a file and write a corresponding text file
    compressed_data = np.fromfile(fname_out, dtype='uint8')
    print("Writing compressed data to txt file:")
    with open(fname_out_txt, 'w') as out:
        for ind in range(0,len(compressed_data)):
            # print(compressed_data[ind])
            out.write(str(compressed_data[ind]) + '\n')

    # Call the 3rd party program to decompress. Note that the file generated is not always identical to
    # the input as for low bit depths (8 or less) the program uses just 8 bits per pixel, and not 16,
    # which is the input format.
    if True:
        maker = "(cd ../../../CometInterceptor/CCSDS/source && make) && cp ../../../CometInterceptor/CCSDS/bin/nebraska.bin nebraska.bin"
        os.system(maker)
        print("Decompressing with nebraska:")
        cmd = f'time ./{nebraska} -b {img_bitdepth} -d {fname_out} -o {"neb_"+fname_decomp}'
        print(cmd)
        os.system(cmd)
        nebraska_decomp_img = np.fromfile("neb_"+fname_decomp, dtype=np.uint16 if img_bitdepth > 8 else np.uint8).reshape([img_height, img_width])

    maker = "(cd ../../../white_dwarf && make 122 1> /dev/null) && cp ../../../white_dwarf/build/bin/ccsds_122_0_b2_decoder ccsds_122_0_b2_decoder"
    os.system(maker)
    print("Decompressing with whitedwarf:")
    print(f'time ./{whitedwarf} {fname_out} {fname_decomp} {whitedwarf_format}')
    os.system(f'time ./{whitedwarf} {fname_out} {fname_decomp} {whitedwarf_format}')
    os.system(f'mv {whitedwarf_format} {fname_decomp}')
    whitedwarf_decomp_img = np.fromfile(fname_decomp, dtype=np.uint16 if img_bitdepth > 8 else np.uint8).reshape([img_height, img_width])

    print("Checking that both decompressors give the same result:")
    decomp_same_result = (nebraska_decomp_img == whitedwarf_decomp_img)
    if decomp_same_result.all():
        print("Decompressors agree.")
    else:
        print("DECOMPRESSORS DISAGREE ON THE OUTPUT!")

    decomp_img = whitedwarf_decomp_img
    print(decomp_img)

    # Do the two match?
    is_match = nebraska_decomp_img == orig_img
    if is_match.all():
        print("A perfect match!")
    else:
        print("ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR")
        print("ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR")
        print("ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR")

    # Print a divider.
    print("*"*20)

    # Display the two original images and then the difference.
    fig, axeslist = plt.subplots(ncols=3, nrows=1)
    axeslist.ravel()[0].imshow(orig_img, cmap=plt.gray())
    axeslist.ravel()[1].imshow(decomp_img, cmap=plt.gray())
    axeslist.ravel()[2].imshow((orig_img-decomp_img) != 0, cmap=plt.gray())
    plt.tight_layout()
    plt.show()

    # Remove the temporary files.
    os.system(f'rm {fname_decomp} {fname_in} {fname_out}')

    print("All good, all matched!")
    print("")


if __name__ == '__main__':

    singletest()
