#include "subband.h"


void subband_scale(int16_t* data, size_t width, size_t height) {

    size_t width_2 = width>>1;
    size_t width_4 = width>>2;
    size_t width_8 = width>>3;

    size_t height_2 = height>>1;
    size_t height_4 = height>>2;
    size_t height_8 = height>>3;

    for(size_t j = 0; j < height_2; ++j) {
        for(size_t i = width_2; i < width; ++i) {
            data[j * width + i] <<= 1;
            data[(j + height_2) * width + i - width_2] <<= 1;
        }
    }

    //Scaling HH_2
    for(size_t j = height_4; j < height_2; ++j) {
        for(size_t i = width_4; i < width_2; ++i) {
            data[j * width + i] <<= 1; 
        }
    }

    //Scaling HL_2 LH_2
    for(size_t j = 0; j < height_4; ++j) {
        for(size_t i = width_4; i < width_2; ++i) {
            data[j * width + i] <<= 2;
            data[(j + height_4) * width + i - width_4] <<= 2;
        }
    }

    //Scaling HH_3
    for(size_t j = height_8; j < height_4; ++j) {
        for(size_t i = width_8; i < width_4; ++i) {
            data[j * width + i] <<= 2;
        }
    }

    //LL_3 HL_3
    for(size_t j = 0; j < height_8; ++j) {
        for(size_t i = 0; i < width_4; ++i) {
            data[j * width + i] <<= 3;
        }
    }

    //LH_3
    for(size_t j = height_8; j < height_4; ++j) {
        for(size_t i = 0; i < width_8; ++i) {
           data[j * width + i] <<= 3; 
        }
    }
}
