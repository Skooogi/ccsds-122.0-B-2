// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#ifndef FILE_IO_H
#define FILE_IO_H

#include "stdint.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifndef LIMIT_COMPRESSION_TO_SMALL_IMAGES
    /// Maximum number of octets of the compressed image. We here assume that
    /// the input image is max 8 MB in size, and the resulting compressed image
    /// is no more than 16 MB in size. (Yes, this is double the original; if
    /// trying to compress random data the result is roughly the same size as
    /// the original, but can in some cases be a bit larger, and we use quite a
    /// bit of margin here.)
    #define MAX_COMPRESSED_DATA_SIZE (16777216UL)
#else
    /// Maximum number of octets of the compressed image. We here assume that
    /// the input image is max 1/8 MB in size, and the resulting compressed image
    /// is no more than 1/4 MB in size. (Yes, this is double the original; if
    /// trying to compress random data the result is roughly the same size as
    /// the original, but can in some cases be a bit larger, and we use quite a
    /// bit of margin here.)
    #define MAX_COMPRESSED_DATA_SIZE (262144UL)
#endif

void file_io_set_compressed_data_addr(uint8_t *Address);

void file_io_write_bits(uint64_t bits, size_t length);
void file_io_close_output_file(void);
uint32_t get_bits_written(void);

size_t file_io_num_bytes_written(void);
uint8_t *file_io_get_compressed_data_ptr(void);

void file_io_clear(void);

#ifdef __cplusplus
}
#endif
#endif //FILE_IO_H
