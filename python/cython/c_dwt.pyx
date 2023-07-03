cimport c_dwt
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
from libc cimport stdint

def c_discrete_wavelet_transform_2D(data, width, height, levels, inverse):
    num_bytes = len(data)
    return _c_dwt_2D(<uint8_t*> data, <int> num_bytes, <size_t> width, <size_t> height, <uint8_t> levels, <uint8_t> inverse)

cdef _c_dwt_2D(uint8_t* src, int num_bytes, width, height, levels, inverse):
    c_dwt.discrete_wavelet_transform_2D(<int32_t*> src, <size_t> width, <size_t> height, <uint8_t> levels, <uint8_t> inverse)
