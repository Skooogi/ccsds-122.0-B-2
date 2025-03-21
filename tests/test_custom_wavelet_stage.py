import numpy as np
import os,sys
sys.path.append(os.path.abspath('../python/cython'))
sys.path.append(os.path.abspath('../python'))
from subband_scaling import rescale
import c_dwt as c_dwt
import struct

if __name__ == '__main__':
    
    width = 32
    height = 32
    bitdepth = 16

    data = np.zeros([width, height], dtype='uint16')
    
    data[:width//8, :height//8] = 2**12
    data[height//4,width//4] = 1

    name = "custom_wavelet.raw"
    name_out = "output.cmp"
    name_decomp = "custom_wavelet_decomp.raw"
    data.tofile(name)

    os.system(f'cd .. && make && cd tests')
    cmd = f'../build/ccsds.bin {name} {name_out} {width} {height} {bitdepth}'
    os.system(cmd)
    os.system('(cd ../python/cython; python3 c_dwt_compile.py build_ext --inplace)')

    #Decomp
    whitedwarf = "ccsds_122_0_b2_decoder"
    whitedwarf_format = 'u16le'
    os.system(f'time ./{whitedwarf} {name_out} {name_decomp} {whitedwarf_format}')
    os.system(f'mv {whitedwarf_format} {name_decomp}')
    whitedwarf_decomp_img = np.fromfile(name_decomp, dtype=np.uint16 if bitdepth > 8 else np.uint8).reshape([height, width])

    #Run wavelet transform to get original data
    #Do DWT in Cython
    levels = 3
    whitedwarf_decomp_img = whitedwarf_decomp_img.flatten()
    c_dwt.c_discrete_wavelet_transform_2D(whitedwarf_decomp_img, width, height, levels, False)
    whitedwarf_decomp_img = whitedwarf_decomp_img.astype(np.uint16).reshape([height, width])
    rescale(data, width, height)
    #end Cython DWT

    is_match = whitedwarf_decomp_img == data
    if is_match.all():
        print("A perfect match!")
    else:
        print("ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR")
        print("ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR")
        print("ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR")
        print(whitedwarf_decomp_img[:16,:16])
        print(data[:16,:16])
