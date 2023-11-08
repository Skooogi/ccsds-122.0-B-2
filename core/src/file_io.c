#include "file_io.h"

#ifndef EMBEDDED
#include <stdio.h>
#include <stdlib.h>
static FILE* fp;
#else
extern void put_word(uint8_t word);
#endif//EMBEDDED

void file_io_write_bits(uint64_t bits, size_t length) {

    static uint8_t cache = 0;
    static uint8_t size = 0;

    for(int32_t i = length - 1; i > -1; --i) {
        cache <<= 1;
        cache |= (bits >> (i)) & 1;
        size++;

        if(size >= 8) {

#ifndef EMBEDDED
            putc(cache, fp);
#else
            put_word(cache);
#endif//EMBEDDED

            cache = 0;
            size = 0;
        }
    }
}

void file_io_set_output_file(const char* filename) {
#ifndef EMBEDDED
    if(!(fp = fopen(filename, "wb"))) {
        printf("Failed to open %s for writing!\n", filename);
        exit(EXIT_FAILURE);
    }
#endif//EMBEDDED
}

void file_io_close_output_file() {
    //Flush cache
    file_io_write_bits(0, 8);
#ifndef EMBEDDED
    fclose(fp);
#endif
}
