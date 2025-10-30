// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#ifndef DWT_H
#define DWT_H

#include <stdint.h>
#include <stddef.h>

void discrete_wavelet_transform_2D(int32_t* data, size_t data_width, size_t data_height, uint8_t transform_levels);

#endif //DWT_H
