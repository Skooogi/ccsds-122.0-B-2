cimport c_dwt
cimport cython
from libc cimport stdint
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy

def c_discrete_wavelet_transform_2D(data, width, height, levels, inverse):

    cdef int16_t* cdata
    cdata = <int16_t *>malloc(width*height*cython.sizeof(int16_t))
    if cdata is NULL:
        raise MemoryError()

    for i in xrange(len(data)):
        cdata[i] = data[i]

    c_dwt.discrete_wavelet_transform_2D(<int16_t*> cdata, <size_t> width, <size_t> height, <uint8_t> levels, <uint8_t> inverse)
    #convert back to python return type
    for i in xrange(len(data)):
        data[i] = cdata[i]

    return data

