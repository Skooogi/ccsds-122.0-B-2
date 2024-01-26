#ifndef DWT_H
#define DWT_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stddef.h>

void discrete_wavelet_transform_2D(int16_t* data, size_t data_width, size_t data_height, uint8_t transform_levels, uint8_t inverse_flag);

#ifdef __cplusplus
}
#endif
#endif //DWT_H
