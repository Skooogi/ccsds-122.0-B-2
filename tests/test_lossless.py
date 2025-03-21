import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pytest

def generate_random_image(max_width, max_height, bitdepth):
    width = np.random.randint(32,max_width)
    width -= width % 8
    height = np.random.randint(32,max_height)
    height -= height % 8

    assert width >= 32 and width % 8 == 0, "Width must be a multiple of eight"
    assert height >= 32 and height % 8 == 0, "Height must be a multiple of eight"
    assert bitdepth > 0 and bitdepth <= 32, "Bitdepth must be between 1 and 32"

    data = np.random.rand(height,width)*2**bitdepth
    return data.astype(np.uint32)

def get_file_bitdepth(bitdepth):
    file_type = np.uint8
    match bitdepth:
        case 1:
            file_type = np.uint8
        case 2:
            file_type = np.uint16
        case 3:
            file_type = np.uint32
        case _:
            print(f'ERROR: Bitdepth {bitdepth} is larger than the max 32.')

    return file_type

@pytest.mark.parametrize('bitdepth', range(1,32))
def test_lossless_end_to_end(bitdepth):
    
    ccsds = "../build/ccsds.bin"

    #Decoders for cross referencing
    nebraska = "./nebraska.bin"
    white_dwarf = "./ccsds_122_0_b2_decoder"

    data_bitdepth = bitdepth
    file_bitdepth = (data_bitdepth+7)//8
    file_type = get_file_bitdepth(bitdepth)
    file_type = np.uint16
    
    data = generate_random_image(1024, 1024, bitdepth).astype(file_type)
    height = data.shape[0]
    width = data.shape[1]

    file_raw = "test.raw" 
    file_compressed = "output.cmp"

    data.tofile(file_raw)
    
    cmd = f'{ccsds} {file_raw} {file_compressed} {width} {height} {data_bitdepth}'
    os.system(cmd)

    #Test file integrity
    cmd = f'{white_dwarf} {file_compressed} white_dwarf.raw u16le'
    os.system(cmd)

    cmd = f'{nebraska} -d {file_compressed} -o nebraska.raw'
    os.system(cmd)

    uncompressed_white_dwarf = np.fromfile("u16le", dtype=file_type)
    assert uncompressed_white_dwarf.size > 0, "White dwarf uncompressing has failed"
    uncompressed_white_dwarf = uncompressed_white_dwarf.reshape([height, width])

    #uncompressed_nebraska = np.fromfile("nebraska.raw", dtype=file_type)
    #assert uncompressed_nebraska.size > 0, "Nebraska uncompressing has failed"
    #uncompressed_nebraska = uncompressed_nebraska.reshape([height, width])

    assert (uncompressed_white_dwarf == data).all(), "Uncompressing losses detected"
    #assert (uncompressed_nebraska == data).all(), "Uncompressing losses detected"
    #plt.imshow(uncompressed)
    #plt.show()

    os.system(f'rm {file_raw} {file_compressed} u16le')
