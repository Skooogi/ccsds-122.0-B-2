This project contains contains an implementation of image compression as 
described in the ccsds_122_B-2 standard as well as some tests for the 
discrete wavelet transform and run length encoder.

----------Makefile----------
Targets:
    all: generates build folder and ccsds.bin
    run: runs the ccsds.bin with default arguments (can be set in makefile)
    debug: runs ccsds.bin through gdb with default arguments
    perf: uses perf to record callgraph data for profiling
    stat: uses perf stat to show runtime data (time, cache misses, cpu utilization)
    valgrind: runs ccsds.bin through the valgrind memcheck tool
    clean: deletes all generated files
Usage:
make target
----------/Makefile----------

----------Python----------
Usage:
python3 ccsds_122.py filein fileout #Takes a bmp image as input and outputs a *.cmp file and out_1.bmp
python3 rccsds_122.py #Uncompresses output.cmp in same folder

Third party:
numpy
Image PIL
struct

Tests:
    test_lossless_random.py #Generates random images and runs ccsds.bin (and ccsds_122.py if enabled) and checks decoded data.
    test_lossless_res.py    #Same as with random except tested images are from the "res" folder
    test_compression_ratio.py #Goes through res images and shows time and compression ratio.(noise images are expected to expand in size)
    test_files.py #Contains common filenames and print colors

/devkit/python includes io_test.py which can be used to test the softare on the SAMV71 Xplained Ultra devkit
The devkit communicates using packets {length = 1 B, data = max 64 B, CRC = 1 B}
Usage:
python3 io_test.py
    - test #Sends a packet and should receive numbers 0-7
    - clear #Clears console
    - file #Sends a file with given width, height and bitdepth. Must be .raw file!
    - compress #Compresses the previously sent file and streams compressed data packets.
    - download #Downloads the sent file data back from the devkit (this data is not compressed)
----------/Python----------


-------------C--------------
bitplane_encoder.c:
    #High level compression code
    TODO:
    - Handle image 16 blocks at a time (currently stores all blocks)

block_transform.c: 
    #From raw pixel data to array of Block structs

common.c: 
    #Math functions and block related functions

discrete_wavelet_transform.c:
    #Forward and reverse DWT
    TODO:
    - Make streaming version that produces blocks one at a time

encoding_stages.c: 
    #Stages [0-4]
    TODO:
    - Clean up and refractor. Some operations are bloat

fifo_queue.c: 
    #Not utilized currently but is for possible future streaming version

file_io.c: 
    #Handles bit level printing and loading data from .raw files

magnitude_encoding.c: 
    #DC and bitAC encoding
    TODO:
    - Clean up code

main.c: 
    #Pads data and runs DWT and bitplane encoder

segment_header.c: 
    #Headers used for holding state and compression settings
    - Check endianness of bitfields on development kit

subband.c: 
    #Scaling of subbands
    TODO:
    - Add user defined weights

word_mapping.c: 
    #Handles mapping words as described in the ccsds standard
-------------/C--------------

//Changes
Fixed heuristic k value calculation in magnitude_encoding.c
Embedded pipeline with python client. Added some ifdefs for file_io.c and main.c Changed long literals from 1L to 1LL
