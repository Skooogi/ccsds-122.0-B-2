// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#ifndef MAGNITUDE_ENCODING_H
#define MAGNITUDE_ENCODING_H

#include "common.h"

#ifdef __cplusplus
extern "C" {
#endif

void magnitude_encoding_set_buffers(int32_t *differences_addr, int32_t *shifted_addr);

void encode_ac_magnitudes(SegmentData* segment_data);
void encode_dc_magnitudes(SegmentData* segment_data);

#ifdef __cplusplus
}
#endif
#endif //MAGNITUDE_ENCODING_H
