cimport c_dwt
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
from libc cimport stdint

def c_discrete_wavelet_transform_2D(data, width, height, levels, inverse):
    num_bytes = len(data)
    return _c_dwt_2D(<uint8_t*> data, <int> num_bytes, <size_t> width, <size_t> height, <uint8_t> levels, <uint8_t> inverse)

cdef _c_dwt_2D(uint8_t* src, int num_bytes, width, height, levels, inverse):
    cdef uint8_t* buff;
    buff = <uint8_t*> malloc(num_bytes)
    memcpy(buff, src, num_bytes)
    c_dwt.discrete_wavelet_transform_2D(<int32_t*> buff, <size_t> width, <size_t> height, <uint8_t> levels, <uint8_t> inverse)
    RET = bytes((<uint8_t*>buff)[:num_bytes])
    free(buff)
    return RET
