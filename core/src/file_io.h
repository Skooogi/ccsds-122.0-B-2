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

void file_io_set_compressed_data_addr(uint8_t *Address, uint32_t Length);

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
