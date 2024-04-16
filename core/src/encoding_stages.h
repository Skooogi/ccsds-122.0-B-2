#ifndef ENCODING_STAGES_H
#define ENCODING_STAGES_H

#include "common.h"
#include "segment_header.h"
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif

void stage_0(SegmentData* segment_data);
void stage_1(SegmentData* segment_data, size_t gaggle_offset, size_t gaggle_size);
void stage_2(SegmentData* segment_data, size_t gaggle_offset, size_t gaggle_size);
void stage_3(SegmentData* segment_data, size_t gaggle_offset, size_t gaggle_size);
void stage_4(SegmentData* segment_data);
#ifdef __cplusplus
}
#endif
#endif //ENCODING_STAGES_H
