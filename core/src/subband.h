#ifndef SUBBAND_H
#define SUBBAND_H

#include "segment_header.h"

#include <stdio.h>
#ifdef	__cplusplus
extern "C" {
#endif

void subband_scale(SegmentHeader* headers, int16_t* data, size_t width, size_t height);

#ifdef __cplusplus
}
#endif
#endif //SUBBAND_H
