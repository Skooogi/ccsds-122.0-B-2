from libc cimport stdint
from libc cimport stddef
from libcpp cimport bool

ctypedef stdint.uint64_t uint64_t
ctypedef stdint.uint32_t uint32_t
ctypedef stdint.uint32_t in_addr_t
ctypedef stdint.int32_t int32_t
ctypedef stdint.uint16_t uint16_t
ctypedef stdint.int16_t int16_t
ctypedef stdint.int16_t q15_t
ctypedef stdint.uint8_t uint8_t
#ctypedef string.bool bool

cdef extern from "discrete_wavelet_transform.h":
    void discrete_wavelet_transform_2D(int32_t* data, size_t data_width, size_t data_height, uint8_t transform_levels, uint8_t inverse_flag)
