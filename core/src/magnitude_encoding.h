#ifndef MAGNITUDE_ENCODING_H
#define MAGNITUDE_ENCODING_H

#include "common.h"

#ifdef __cplusplus
extern "C" {
#endif

void encode_ac_magnitudes(SegmentData* segment_data);
void encode_dc_magnitudes(SegmentData* segment_data);

#ifdef __cplusplus
}
#endif
#endif //MAGNITUDE_ENCODING_H
