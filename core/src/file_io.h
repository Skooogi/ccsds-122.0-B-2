#ifndef FILE_IO_H
#define FILE_IO_H

#include "stdint.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

void file_io_set_output_file(const char* filename);
void file_io_write_bits(uint64_t bits, size_t length);
void file_io_close_output_file();
uint32_t get_bits_written();

#ifdef __cplusplus
}
#endif
#endif //FILE_IO_H
