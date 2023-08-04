#include "bitplane_encoder.h"
#include "discrete_wavelet_transform.h"
#include "file_io.h"
#include "segment_header.h"
#include "subband.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char** argv) {

    char* filename = argv[1];
    char* end;
    int32_t side_length = strtol(argv[2], &end, 10);

    FILE* fp = fopen(filename, "rb");
    if(!fp) {
        printf("Can not open file %s", filename);
 
        return 1;
    }

    int32_t* test_data = malloc(side_length*side_length*sizeof(int32_t));
    fread(test_data, sizeof(int32_t), side_length*side_length, fp);
    fclose(fp);


    //Save output
    file_io_set_output_file("../python/output.cmp") ;
    SegmentHeader* headers = segment_header_init_values();
    //TEST PARAMETERS START
    headers->header_1.first_segment = 1;
    headers->header_1.last_segment = 1;
    headers->header_1.num_segments = 1;
    headers->header_1.has_header_3 = 1;
    headers->header_1.has_header_4 = 1;

    headers->header_3.segment_size = (side_length>>3)*(side_length>>3);

    headers->header_4.dwt_type = 1;
    headers->header_4.pixel_bitdepth = 8;
    headers->header_4.image_width = side_length;
    //TEST PARAMETERS END
    
    discrete_wavelet_transform_2D(test_data, side_length, side_length, 3, 0);

    subband_scale(test_data, side_length, side_length);

    bitplane_encoder_encode(test_data, headers);

    file_io_close_output_file();
    free(test_data);
	return 0;
}
