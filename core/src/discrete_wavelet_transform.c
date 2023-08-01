#include "discrete_wavelet_transform.h"
#include <stdint.h>
#include <string.h>
#include <stdio.h>


//Fast floating point conversion from http://stereopsis.com/FPU.html
static const float _double2fixmagic = 68719476736.0*1.5;     //2^36 * 1.5,  (52-_shiftamt=36) uses limited precisicion to floor
static const int32_t _shiftamt      = 16;                    //16.16 fixed point representation
static inline int32_t to_int(float value) {
    value = value + _double2fixmagic;
	return ((int32_t*)&value)[0] >> _shiftamt;
}

//Multiplication is faster than division
static const float per16 = 0.0625f;
static const float per8 = 0.125f;
static const float per4 = 0.25f;

static void forward_DWT(int32_t* data, size_t width) {

	//cache line for in place operation
	int32_t cache[width];
	memcpy(&cache, data, width * sizeof(int32_t));

	uint32_t n = width >> 1; //number of coefficients in pass
	int32_t* highpass = &data[n];
	int32_t* lowpass = &data[0];

    highpass[0] = cache[1] - to_int((9 * (cache[0] + cache[2]) - (cache[2] + cache[4])) * per16 + 0.5);
    lowpass[0] = cache[0] - to_int(-highpass[0]*0.5 + 0.5);

    highpass[n-2] = cache[2*n-3] - to_int((9 * (cache[2*n-4] + cache[2*n-2]) - (cache[2*n-6] + cache[2*n-2])) * per16 + 0.5);
    highpass[n-1] = cache[2*n-1] - to_int((9 * cache[2*n-2] - cache[2*n-4]) * per8 + 0.5);

	for(size_t i = 1; i < n - 2; ++i) {
        highpass[i] = cache[2*i+1] - to_int((9 * (cache[2*i] + cache[2*i+2]) - (cache[2*i-2] + cache[2*i+4])) * per16 + 0.5);
        lowpass[i] = cache[2*i] - to_int(-(highpass[i-1] + highpass[i]) * per4 + 0.5);
	}

    lowpass[n-2] = cache[2*n-4] - to_int(-(highpass[n-3] + highpass[n-2]) * per4 + 0.5);
    lowpass[n-1] = cache[2*n-2] - to_int(-(highpass[n-2] + highpass[n-1]) * per4 + 0.5);
}

static void backward_DWT(int32_t* data, size_t width) {

    size_t n = width >> 1;
    int32_t cache[width];
	int32_t* lowpass = &cache[0];
	int32_t* highpass = &cache[n];
    memcpy(&cache, data, width * sizeof(int32_t));
    
    data[0] = lowpass[0] + to_int(-highpass[0]*0.5 + 0.5);

    for(size_t i = 1; i < n; ++i) {
        data[2*(i+0)] = lowpass[i+0] + to_int(-(highpass[i-1]+highpass[i+0])*per4 + 0.5);
	}

    data[1] = highpass[0] + to_int(9.f/16*(data[0] + data[2])-1.f/16*(data[2] + data[4]) + 0.5);

    for(size_t i = 1; i < n - 2; ++i) {
        data[2*i+1] = highpass[i] + to_int(9.f/16*(data[2*i] + data[2*i+2]) - 1.f/16*(data[2*i-2] + data[2*i+4]) + 0.5);
	}
    
    data[2*n-3] = highpass[n-2] + to_int(9.f/16*(data[2*n-4] + data[2*n-2]) - 1.f/16*(data[2*n-6] + data[2*n-2]) + 0.5);
    data[2*n-1] = highpass[n-1] + to_int(9.f/8*data[2*n-2] - 1.f/8*data[2*n-4] + 0.5);
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
