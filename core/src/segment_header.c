#include "segment_header.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

SegmentHeader* segment_header_init_values(void) {
    
    SegmentHeader* headers = malloc(sizeof(SegmentHeader));
    memset(headers, 0, sizeof(SegmentHeader));

    return headers;
}

static void write_bits(uint64_t bits, size_t length, FILE* fp) {

    static uint8_t cache = 0;
    static uint8_t size = 0;
    for(int32_t i = length - 1; i > -1; --i) {
        cache <<= 1;
        cache |= (bits >> (i)) & 1;
        size++;

        if(size >= 8) {
            putc(cache, fp);
            cache = 0;
            size = 0;
        }
    }
}

void segment_header_write_data(SegmentHeader* headers, FILE* fp) {
    
    write_bits(headers->header_1.packed, 32, fp);
    if(headers->header_1.has_header_2) {
        write_bits(headers->header_2.packed, 40, fp);
    }
    if(headers->header_1.has_header_3) {
        write_bits(headers->header_3.packed, 24, fp);
    }
    if(headers->header_1.has_header_4) {
        printf("%lu\n", headers->header_4.packed);
        write_bits(headers->header_4.packed, 64, fp);
    }
}
