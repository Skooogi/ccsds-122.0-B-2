#include "discrete_wavelet_transform.h"
#include "segment_header.h"
#include <stdio.h>
#include <stdlib.h>


//#define STB_IMAGE_IMPLEMENTATION
//#include "stb_image.h"
//#define STB_IMAGE_WRITE_IMPLEMENTATION
//#include "stb_image_write.h"

extern int32_t test_data;

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

    discrete_wavelet_transform_2D(test_data, side_length, side_length, 3, 0);

    //Save output
    FILE* output_fp = fopen("../python/output.cmp", "wb");
    if(!output_fp) {
        printf("Can not open output.cmp for writing!\n");
        return 1;
    }

    SegmentHeader* headers = segment_header_init_values();

    //TEST PARAMETERS START

    //TEST PARAMETERS END
    
    segment_header_write_data(headers, output_fp);
    fwrite(test_data, side_length*side_length, sizeof(int32_t), output_fp);
    fclose(output_fp);

    free(test_data);
	return 0;
}
