import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pytest

def generate_random_image(width, height, bitdepth, seed):
    np.random.seed(seed)
    assert width >= 32 and width % 8 == 0, "Width must be a multiple of eight"
    assert height >= 32 and height % 8 == 0, "Height must be a multiple of eight"
    assert bitdepth > 0 and bitdepth <= 25, "Bitdepth must be between 1 and 32"

    data = np.random.rand(height,width)*(2**bitdepth)
    return data.astype(np.uint32)

def generate_16_by_nine(size, bitdepth, seed):

    width = 32
    height = 32
    return generate_random_image(width*size,height*size, bitdepth, seed)

def compress_image(filename, width, height, bitdepth):
    ccsds = "../build/ccsds.bin"
    file_compressed = "output.cmp"

    cmd = f'time {ccsds} {filename} {file_compressed} {width} {height} {bitdepth}'
    os.system(cmd)

def decompress_and_check_integrity(data, width, height):
    #Decoders for cross referencing
    nebraska = "./nebraska.bin"
    white_dwarf = "./ccsds_122_0_b2_decoder"
    file_type = np.uint32

    #Test file integrity
    white_dwarf_type = "u32le"
    cmd = f'time {white_dwarf} output.cmp white_dwarf.raw {white_dwarf_type}'
    os.system(cmd)

    uncompressed_white_dwarf = np.fromfile(white_dwarf_type, dtype=file_type)
    assert uncompressed_white_dwarf.size > 0, "White dwarf uncompressing has failed"
    uncompressed_white_dwarf = uncompressed_white_dwarf.reshape([height, width])

    #(a == b).all() fails if data is 20bit or more
    return ((uncompressed_white_dwarf-data) == 0).all()

@pytest.mark.parametrize("seed", range(1))
@pytest.mark.parametrize("bitdepth", range(1,26))
@pytest.mark.parametrize("size", range(1,11))
def test_lossless_16_by_9(size, bitdepth, seed):
    
    file_raw = "test.raw" 

    data = generate_16_by_nine(size, bitdepth,1)
    height = data.shape[0]
    width = data.shape[1]

    data.tofile(file_raw)

    compress_image(file_raw, width, height, bitdepth)
    assert decompress_and_check_integrity(data, width, height) == True, "Uncompression failed"
    os.system(f'rm {file_raw} output.cmp u32le')



