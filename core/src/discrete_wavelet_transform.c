#include "discrete_wavelet_transform.h"
#include <math.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>

static inline int32_t to_int(float value) { return (int)(value - (value < 0 && value != (int) value)); }

//Precomputed coefficients for faster multiplication
static float o_16 = -1.f/16;
static float o_8 = -1.f/8;
static float n_16 = 9.f/16;
static float n_8 = 9.f/8;

static void forward_DWT(int32_t* data, size_t width) {

	//Copy line for in place operating
	int32_t cache[width+1];
	memcpy(&cache, data, width * sizeof(int32_t));
	uint32_t n_coeffs = width >> 1;
	int32_t highpass[n_coeffs + 1];

	highpass[0] = cache[1] - to_int(n_16 * (cache[0]+cache[2]) + o_16 * (cache[2]+cache[4]) + 0.5);

	for(size_t i = 1; i < n_coeffs - 2; i+=4) {

        uint32_t c_2 = cache[2*i-2];
        uint32_t c_1 = cache[2*i-1];
        uint32_t c0 = cache[2*i];
        uint32_t c1 = cache[2*i+1];
        uint32_t c2 = cache[2*i+2];
        uint32_t c3 = cache[2*i+3];
        uint32_t c4 = cache[2*i+4];
        uint32_t c5 = cache[2*i+5];
        uint32_t c6 = cache[2*i+6];
        uint32_t c7 = cache[2*i+7];

		highpass[i]   = cache[c1] - to_int(n_16*(cache[c0]+cache[c2]) + o_16*(cache[c_2]+cache[c4]) + 0.5);
		highpass[i+1] = cache[c2] - to_int(n_16*(cache[c1]+cache[c3]) + o_16*(cache[c_1]+cache[c5]) + 0.5);
		highpass[i+2] = cache[c3] - to_int(n_16*(cache[c2]+cache[c4]) + o_16*(cache[c0]+cache[c6]) + 0.5);
		highpass[i+3] = cache[c4] - to_int(n_16*(cache[c3]+cache[c5]) + o_16*(cache[c1]+cache[c7]) + 0.5);
	}

    highpass[n_coeffs-2] = cache[2*n_coeffs-3] - to_int(n_16*(cache[2*n_coeffs-4]+cache[2*n_coeffs-2])  + o_16*(cache[2*n_coeffs-6]+cache[2*n_coeffs-2]) + 0.5);

    highpass[n_coeffs-1] = cache[2*n_coeffs-1] - to_int(n_8*cache[2*n_coeffs-2] + o_8*cache[2*n_coeffs-4] + 0.5);

    data[0] = cache[0] - to_int(-highpass[0]*0.5 + 0.5);
	data[n_coeffs] = highpass[0];
    for(size_t i = 1; i < n_coeffs; ++i) {
        data[i] = cache[2*i] - to_int(-(highpass[i-1]+highpass[i])*0.25 + 0.5);
		data[n_coeffs+i] = highpass[i];
	}
}

static void backward_DWT(int32_t* data, size_t width) {

    size_t n_coeffs = width >> 1;
	int32_t lowpass[n_coeffs];
	int32_t highpass[n_coeffs];
	memcpy(&lowpass, data, n_coeffs * sizeof(int32_t));
	memcpy(&highpass, data + n_coeffs, n_coeffs * sizeof(int32_t));
    
    data[0] = lowpass[0] + to_int(-highpass[0]*0.5 + 0.5);

    for(size_t i = 1; i < n_coeffs; ++i) {
        data[2*i] = lowpass[i] + to_int(-(highpass[i-1]+highpass[i])*0.25 + 0.5);
	}

    data[1] = highpass[0] + to_int(9.f/16*(data[0] + data[2])-1.f/16*(data[2] + data[4]) + 0.5);

    for(size_t i = 1; i < n_coeffs - 2; ++i) {
        data[2*i+1] = highpass[i] + to_int(9.f/16*(data[2*i] + data[2*i+2]) - 1.f/16*(data[2*i-2] + data[2*i+4]) + 0.5);
	}
    
    data[2*n_coeffs-3] = highpass[n_coeffs-2] + to_int(9.f/16*(data[2*n_coeffs-4] + data[2*n_coeffs-2]) - 1.f/16*(data[2*n_coeffs-6] + data[2*n_coeffs-2]) + 0.5);

    data[2*n_coeffs-1] = highpass[n_coeffs-1] + to_int(9.f/8*data[2*n_coeffs-2] - 1.f/8*data[2*n_coeffs-4] + 0.5);
}

void discrete_wavelet_transform_2D(int32_t* data, size_t data_width, size_t data_height, uint8_t transform_levels, uint8_t inverse_flag) {

    if(inverse_flag) {
        for(int8_t level = transform_levels-1; level >= 0; --level) {
            uint32_t current_width = data_width >> level;
            uint32_t current_height = data_height >> level;

            //Vertical
			uint32_t temp_column[current_height];
            for(uint32_t column = 0; column < current_width; ++column) {

				//Copy current column to temp_column
				for(uint32_t row = 0;  row < current_height; ++row) {
					//Each iteration overwrites temp_column
					temp_column[row] = data[row * data_width + column];
				}

				backward_DWT((int32_t*)&temp_column, current_height);

				for(uint32_t row = 0;  row < current_height; ++row) {
					data[row * data_width + column] = temp_column[row];
				}
			}

            //Horizontal
			int32_t temp_row[current_width];
			//Iterate each row
            for(uint32_t row = 0; row < current_height; ++row) {

				//Copy current row to temp_row
				for(uint32_t column = 0;  column < current_width; ++column) {
					temp_row[column] = data[row * data_width + column];
				}

                backward_DWT((int32_t*)&temp_row, current_width);

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
		int32_t temp_row[current_width];
		//Iterate each row
		for(uint32_t row = 0; row < current_height; ++row) {

			//Copy current row to temp_row
			for(uint32_t column = 0;  column < current_width; ++column) {
				temp_row[column] = data[row * data_width + column];
			}

			forward_DWT((int32_t*)&temp_row, current_width);

			for(uint32_t column = 0;  column < current_width; ++column) {
				data[row * data_width + column] = temp_row[column];
			}
		}

		//Vertical
		int32_t temp_column[current_height];
		for(uint32_t column = 0; column < current_width; ++column) {

			//Copy current column to temp_column
			for(uint32_t row = 0;  row < current_height; ++row) {
				//Each iteration overwrites temp_column
				temp_column[row] = data[row * data_width + column];
			}

			forward_DWT((int32_t*)&temp_column, current_height);

			for(uint32_t row = 0;  row < current_height; ++row) {
				data[row * data_width + column] = temp_column[row];
			}
		}
	}
}
