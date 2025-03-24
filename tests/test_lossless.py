import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pytest

def generate_random_image(max_width, max_height, bitdepth, seed):
    np.random.seed(seed)
    width = np.random.randint(32,max_width)
    width -= width % 8
    height = np.random.randint(32,max_height)
    height -= height % 8

    assert width >= 32 and width % 8 == 0, "Width must be a multiple of eight"
    assert height >= 32 and height % 8 == 0, "Height must be a multiple of eight"
    assert bitdepth > 0 and bitdepth <= 25, "Bitdepth must be between 1 and 32"

    data = np.random.rand(height,width)*2**bitdepth
    return data.astype(np.uint32)

def get_file_bitdepth(bitdepth):
    file_type = np.uint8
    match (bitdepth+7)//8:
        case 1:
            file_type = np.uint8
        case 2:
            file_type = np.uint16
        case 3:
            file_type = np.uint32
        case _:
            print(f'ERROR: Bitdepth {bitdepth} is larger than the max 32.')

    return file_type

@pytest.mark.parametrize('seed', range(3))
@pytest.mark.parametrize('bitdepth', range(8,9))
def test_lossless_end_to_end(bitdepth, seed):
    
    ccsds = "../build/ccsds.bin"

    #Decoders for cross referencing
    nebraska = "./nebraska.bin"
    white_dwarf = "./ccsds_122_0_b2_decoder"

    file_type = np.uint32
    
    data = generate_random_image(1920, 1080, bitdepth, seed).astype(file_type)
    height = data.shape[0]
    width = data.shape[1]

    file_raw = "test.raw" 
    file_compressed = "output.cmp"

    data.tofile(file_raw)
    
    print("Compression")
    cmd = f'time {ccsds} {file_raw} {file_compressed} {width} {height} {bitdepth}'
    os.system(cmd)

    #Test file integrity
    white_dwarf_type = "u32le"
    print("Decompression")
    cmd = f'time {white_dwarf} {file_compressed} white_dwarf.raw {white_dwarf_type}'
    os.system(cmd)

    cmd = f'{nebraska} -d {file_compressed} -o nebraska.raw'
    os.system(cmd)

    uncompressed_white_dwarf = np.fromfile(white_dwarf_type, dtype=file_type)
    assert uncompressed_white_dwarf.size > 0, "White dwarf uncompressing has failed"
    uncompressed_white_dwarf = uncompressed_white_dwarf.reshape([height, width])

    assert (uncompressed_white_dwarf == data).all(), "Uncompressing losses detected"
    os.system(f'rm {file_raw} {file_compressed} {white_dwarf_type}')
