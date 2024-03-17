#include "discrete_wavelet_transform.h"
#include <stdint.h>
#include <string.h>
#include <stdio.h>

static inline int16_t round_int(int32_t numerator, int32_t denominator) {
    return (numerator) < 0 ? ((numerator) - ((denominator)/2)) / (denominator) : ((numerator) + ((denominator)/2)) / (denominator);
}

/*
static inline int16_t round_int(int32_t numerator, int32_t denominator) {

    float temp = ((float)numerator/denominator) + 0.5f;
    if(temp < 0) {
        if(temp != (int)temp) {
            temp -= 1;
        }
    }    
    return (int16_t)temp;
}
*/
static void forward_DWT(int16_t* data, size_t width) {

	//cache line for in place operation
	int16_t cache[width];
	memcpy(&cache, data, width * sizeof(int16_t));

	uint32_t n = width >> 1; //number of coefficients in pass
	int16_t* highpass = &data[n];
	int16_t* lowpass = &data[0];

    highpass[0] = cache[1] - round_int((9 * (cache[0] + cache[2]) - (cache[2] + cache[4])), 16);
    lowpass[0] = cache[0] - round_int(-highpass[0], 2);

    highpass[n-2] = cache[2*n-3] - round_int((9 * (cache[2*n-4] + cache[2*n-2]) - (cache[2*n-6] + cache[2*n-2])), 16);
    highpass[n-1] = cache[2*n-1] - round_int((9 * cache[2*n-2] - cache[2*n-4]), 8);

	for(size_t i = 1; i < n - 2; ++i) {
        highpass[i] = cache[2*i+1] - round_int((9 * (cache[2*i] + cache[2*i+2]) - (cache[2*i-2] + cache[2*i+4])), 16);
        lowpass[i] = cache[2*i] - round_int(-(highpass[i-1] + highpass[i]), 4);
	}

    lowpass[n-2] = cache[2*n-4] - round_int(-(highpass[n-3] + highpass[n-2]), 4);
    lowpass[n-1] = cache[2*n-2] - round_int(-(highpass[n-2] + highpass[n-1]), 4);
}

static void backward_DWT(int16_t* data, size_t width) {

    size_t n = width >> 1;
    int16_t cache[width];
	int16_t* lowpass = &cache[0];
	int16_t* highpass = &cache[n];
    memcpy(&cache, data, width * sizeof(int16_t));
    
    data[0] = lowpass[0] + round_int(-highpass[0], 2);

    for(size_t i = 1; i < n; ++i) {
        data[2*(i+0)] = lowpass[i+0] + round_int(-(highpass[i-1]+highpass[i+0]), 4);
	}

    data[1] = highpass[0] + round_int(9 *(data[0] + data[2]) - (data[2] + data[4]), 16);

    for(size_t i = 1; i < n - 2; ++i) {
        data[2*i+1] = highpass[i] + round_int(9 * (data[2*i] + data[2*i+2]) - (data[2*i-2] + data[2*i+4]), 16);
	}
    
    data[2*n-3] = highpass[n-2] + round_int(9 * (data[2*n-4] + data[2*n-2]) - (data[2*n-6] + data[2*n-2]), 16);
    data[2*n-1] = highpass[n-1] + round_int(9 * data[2*n-2] - data[2*n-4], 8);
}

void discrete_wavelet_transform_2D(int16_t* data, size_t data_width, size_t data_height, uint8_t transform_levels, uint8_t inverse_flag) {

    if(inverse_flag) {
        for(int8_t level = transform_levels-1; level >= 0; --level) {
            uint32_t current_width = data_width >> level;
            uint32_t current_height = data_height >> level;

            //Vertical
			int16_t temp_column[current_height];
            for(uint32_t column = 0; column < current_width; ++column) {

				//Copy current column to temp_column
				for(uint32_t row = 0;  row < current_height; ++row) {
					//Each iteration overwrites temp_column
					temp_column[row] = data[row * data_width + column];
				}

				backward_DWT((int16_t*)&temp_column, current_height);

				for(uint32_t row = 0;  row < current_height; ++row) {
					data[row * data_width + column] = temp_column[row];
				}
			}

            //Horizontal
			int16_t temp_row[current_width];
			//Iterate each row
            for(uint32_t row = 0; row < current_height; ++row) {

				//Copy current row to temp_row
				for(uint32_t column = 0;  column < current_width; ++column) {
					temp_row[column] = data[row * data_width + column];
				}

                backward_DWT((int16_t*)&temp_row, current_width);

				for(uint32_t column = 0;  column < current_width; ++column) {
					data[row * data_width + column] = temp_row[column];
				}
			}

		}
		return;
	}

	for(uint8_t level = 0; level < transform_levels; ++level) {
		uint32_t current_width = data_width >> level;
		uint32_t current_height = data_height >> level;

		
		//Horizontal
		int16_t temp_row[current_width];
		//Iterate each row
		for(uint32_t row = 0; row < current_height; ++row) {

			//Copy current row to temp_row
			for(uint32_t column = 0;  column < current_width; ++column) {
				temp_row[column] = data[row * data_width + column];
			}

			forward_DWT((int16_t*)&temp_row, current_width);

			for(uint32_t column = 0;  column < current_width; ++column) {
				data[row * data_width + column] = temp_row[column];
			}
		}

		//Vertical
		int16_t temp_column[current_height];
		for(uint32_t column = 0; column < current_width; ++column) {

			//Copy current column to temp_column
			for(uint32_t row = 0;  row < current_height; ++row) {
				//Each iteration overwrites temp_column
				temp_column[row] = data[row * data_width + column];
			}

			forward_DWT((int16_t*)&temp_column, current_height);

			for(uint32_t row = 0;  row < current_height; ++row) {
				data[row * data_width + column] = temp_column[row];
			}
		}
	}
}
