#ifndef SEGMENT_HEADER_H
#define SEGMENT_HEADER_H

#ifdef	__cplusplus
extern "C" {
#endif

#include <stdint.h>

//TODO check endianness so that bitfields are packer in correct order;

//4 Bytes
typedef struct Header_1 {

    unsigned first_segment  : 1;
    unsigned last_segment   : 1;
    unsigned num_segments   : 8;
    unsigned bitDC          : 5;
    unsigned bitAC          : 5;

    unsigned reserved_1     : 1;
    unsigned has_header_2   : 1;
    unsigned has_header_3   : 1;
    unsigned has_header_4   : 1;

    unsigned pad_width      : 3;
    unsigned reserved_2     : 5;

} Header_1;

//5 Bytes
typedef struct Header_2 {
    
    unsigned seg_byte_limit : 27;
    unsigned dc_stop        : 1;
    unsigned bitplane_stop  : 5;
    unsigned stage_stop     : 2;
    unsigned use_fill       : 1;
    unsigned reserved_1     : 4;
} Header_2;

//3 Bytes
typedef struct Header_3 {
    
   unsigned segment_size        : 20;
   unsigned optimal_dc_select   : 1;
   unsigned optimal_ac_select   : 1;
   unsigned reserved_1          : 2;
} Header_3;


//8 Bytes
typedef struct Header_4 {
    
    unsigned dwt_type               : 1;
    unsigned reserved_1             : 1;
    unsigned extended_pixel_depth   : 1;
    unsigned signed_pixels          : 1;
    unsigned pixel_bitdepth         : 4;
    unsigned image_width            : 20;
    unsigned transpose_image        : 1;
    unsigned code_word_length       : 3;

    unsigned custom_weights         : 1;
    unsigned custom_weight_HH_1     : 2;
    unsigned custom_weight_HL_1     : 2;
    unsigned custom_weight_LH_1     : 2;
    unsigned custom_weight_HH_2     : 2;
    unsigned custom_weight_HL_2     : 2;
    unsigned custom_weight_LH_2     : 2;
    unsigned custom_weight_HH_3     : 2;
    unsigned custom_weight_HL_3     : 2;
    unsigned custom_weight_LH_3     : 2;
    unsigned custom_weight_LL_3     : 2;
    unsigned reserved_2             : 11;
} Header_4;

typedef struct {

    Header_1 header_1;
    Header_2 header_2;
    Header_3 header_3;
    Header_4 header_4;

} SegmentHeader;

SegmentHeader* segment_header_init_values(void);

#ifdef	__cplusplus
}
#endif
#endif //SEGMENT_HEADER_H
