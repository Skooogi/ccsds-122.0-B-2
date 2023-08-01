#include "segment_header.h"
#include <stdlib.h>

SegmentHeader* segment_header_init_values(void) {
    
    SegmentHeader* headers = calloc(1, sizeof(SegmentHeader));
    
    headers->header_1.first_segment    = 1;
    headers->header_1.last_segment     = 1;
    headers->header_1.num_segments     = 1;
    headers->header_1.has_header_3     = 1;
    headers->header_1.has_header_4     = 1;

    return headers;
}
