#include "file_io.h"
#include "segment_header.h"
#include <stdlib.h>
#include <string.h>

SegmentHeader* segment_header_init_values(void) {
    
    SegmentHeader* headers = malloc(sizeof(SegmentHeader));
    memset(headers, 0, sizeof(SegmentHeader));

    return headers;
}

void segment_header_write_data(SegmentHeader* headers) {
    if(!headers->header_1.last_segment) {
        file_io_write_bits(headers->header_1.packed >> 8, 24);
    }
    else {
        file_io_write_bits(headers->header_1.packed, 32);
    }
    if(headers->header_1.has_header_2) {
        file_io_write_bits(headers->header_2.packed, 40);
    }
    if(headers->header_1.has_header_3) {
        file_io_write_bits(headers->header_3.packed, 24);
    }
    if(headers->header_1.has_header_4) {
        file_io_write_bits(headers->header_4.packed, 64);
    }
}
