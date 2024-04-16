#include "subband.h"
#include "segment_header.h"

void subband_scale(SegmentHeader* headers, int16_t* data, size_t width, size_t height) {

    size_t width_2 = width>>1;
    size_t width_4 = width>>2;
    size_t width_8 = width>>3;

    size_t height_2 = height>>1;
    size_t height_4 = height>>2;
    size_t height_8 = height>>3;
    
    uint8_t HH_1 = 0;
    uint8_t HL_1 = 1;
    uint8_t LH_1 = 1;
    uint8_t HH_2 = 1;
    uint8_t HL_2 = 2;
    uint8_t LH_2 = 2;
    uint8_t HH_3 = 2;
    uint8_t HL_3 = 3;
    uint8_t LH_3 = 3;
    uint8_t LL_3 = 3;

    if(headers->header_4.custom_weights) {
        HH_1 = headers->header_4.custom_weight_HH_1;
        HL_1 = headers->header_4.custom_weight_HL_1;
        LH_1 = headers->header_4.custom_weight_LH_1;
        HH_2 = headers->header_4.custom_weight_HH_2;
        HL_2 = headers->header_4.custom_weight_HL_2;
        LH_2 = headers->header_4.custom_weight_LH_2;
        HH_3 = headers->header_4.custom_weight_HH_3;
        HL_3 = headers->header_4.custom_weight_HL_3;
        LH_3 = headers->header_4.custom_weight_LH_3;
        LL_3 = headers->header_4.custom_weight_LL_3;
    }

    //Scaling HH_1
    for(size_t j = height_2; j < height; ++j) {
        for(size_t i = width_2; i < width; ++i) {
            data[j * width + i] <<= HH_1;
        }
    }

    //HL_1
    for(size_t j = 0; j < height_2; ++j) {
        for(size_t i = width_2; i < width; ++i) {
            data[j * width + i] <<= HL_1;
        }
    }

    //LH_1
    for(size_t j = height_2; j < height; ++j) {
        for(size_t i = 0; i < width_2; ++i) {
           data[j * width + i] <<= LH_1; 
        }
    }
    //Scaling HH_2
    for(size_t j = height_4; j < height_2; ++j) {
        for(size_t i = width_4; i < width_2; ++i) {
            data[j * width + i] <<= HH_2;
        }
    }

    //HL_2
    for(size_t j = 0; j < height_4; ++j) {
        for(size_t i = width_4; i < width_2; ++i) {
            data[j * width + i] <<= HL_2;
        }
    }

    //LH_2
    for(size_t j = height_4; j < height_2; ++j) {
        for(size_t i = 0; i < width_4; ++i) {
           data[j * width + i] <<= LH_2; 
        }
    }

    //Scaling HH_3
    for(size_t j = height_8; j < height_4; ++j) {
        for(size_t i = width_8; i < width_4; ++i) {
            data[j * width + i] <<= HH_3;
        }
    }

    //HL_3
    for(size_t j = 0; j < height_8; ++j) {
        for(size_t i = width_8; i < width_4; ++i) {
            data[j * width + i] <<= HL_3;
        }
    }

    //LH_3
    for(size_t j = height_8; j < height_4; ++j) {
        for(size_t i = 0; i < width_8; ++i) {
           data[j * width + i] <<= LH_3; 
        }
    }

    //LL_3
    for(size_t j = 0; j < height_8; ++j) {
        for(size_t i = 0; i < width_8; ++i) {
            data[j * width + i] <<= LL_3;
        }
    }
}
