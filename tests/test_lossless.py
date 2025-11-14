from common_test_functions import *

@pytest.mark.parametrize('seed', range(10))
@pytest.mark.parametrize('bitdepth', range(1, 13))
def test_lossless_end_to_end(bitdepth, seed):
    
    ccsds = "../build/ccsds.bin"

    #Decoders for cross referencing
    nebraska = "./nebraska.bin"
    white_dwarf = "./ccsds_122_0_b2_decoder"

    file_type = np.uint32
    
    data = generate_random_image(64, 64, bitdepth, seed).astype(file_type)
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

    #cmd = f'{nebraska} -d {file_compressed} -o nebraska.raw'
    #os.system(cmd)

    uncompressed_white_dwarf = np.fromfile(white_dwarf_type, dtype=file_type)
    assert uncompressed_white_dwarf.size > 0, "White dwarf uncompressing has failed"
    uncompressed_white_dwarf = uncompressed_white_dwarf.reshape([height, width])

    print(uncompressed_white_dwarf)
    print(data)
    assert (uncompressed_white_dwarf == data).all(), "Uncompressing losses detected"
    os.system(f'rm {file_raw} {file_compressed} {white_dwarf_type}')

