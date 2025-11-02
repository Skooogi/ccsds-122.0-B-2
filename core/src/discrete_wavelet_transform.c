// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#include "discrete_wavelet_transform.h"
#include <stdint.h>
#include <string.h>

#define MAX_WIDTH (2048)

static int32_t cache[MAX_WIDTH];

static int32_t temp_row[MAX_WIDTH];

static int32_t temp_column[MAX_WIDTH];


static void forward_DWT(int32_t* data, size_t width) {
    //An array of size W [0.....W] is transformed to highpass 'H' and lowpass 'L' values.
    //The transformation is in-place and the resulting array is formed as:
    //[L_0,L_1 ... L_(W/2), H_0, H1 ... H_(W/2)]
    //
    //The transformation is calculated as shown in (3.3.2)

	//cache line for in place operation
	memcpy(&cache, data, width * sizeof(int32_t));

	uint32_t n = (uint32_t) width >> 1; //number of coefficients in pass
	int32_t* highpass = &data[n];
	int32_t* lowpass = &data[0];

	// Below, we utilize the fact that a right-shift operation ">>" by a positive integer N, on a
	// signed (also negative) argument, performs division by 2**N and subsequent floor (i.e. rounding
	// towards negative infinity). This is not guaranteed by the C standard (which leaves this behavior
	// as implementation-defined) but has been confirmed on both the target and on the WSTE. (This
	// flooring behavior of right-shift, i.e. arithmetical shift, is typical on all major platforms.)

    highpass[0] = (int32_t) (cache[1] - ((9 * (cache[0] + cache[2]) - (cache[2] + cache[4]) + 8) >> 4));
    lowpass[0] = (int32_t) (cache[0] - ((-highpass[0] + 1) >> 1));

    highpass[n-2] = (int32_t) (cache[2*n-3] - ((9 * (cache[2*n-4] + cache[2*n-2]) - (cache[2*n-6] + cache[2*n-2]) + 8) >> 4));
    highpass[n-1] = (int32_t) (cache[2*n-1] - ((9 * cache[2*n-2] - cache[2*n-4] + 4) >> 3));

	for(size_t i = 1; i < n - 2; ++i) {
        highpass[i] = (int32_t) (cache[2*i+1] - ((9 * (cache[2*i] + cache[2*i+2]) - (cache[2*i-2] + cache[2*i+4]) + 8) >> 4));
        lowpass[i] = (int32_t) (cache[2*i] - ((-(highpass[i-1] + highpass[i]) + 2) >> 2));
	}

    lowpass[n-2] = (int32_t) (cache[2*n-4] - ((-(highpass[n-3] + highpass[n-2]) + 2) >> 2));
    lowpass[n-1] = (int32_t) (cache[2*n-2] - ((-(highpass[n-2] + highpass[n-1]) + 2) >> 2));
}


void discrete_wavelet_transform_2D(int32_t* data, size_t data_width, size_t data_height, uint8_t transform_levels) {
    //The 2D-image is split into 1D rows and columns.
    //These 1D arrays are operated on independantly.
    //The resulting 2D lowpass area is then transformed.
    //This is repeated 3 times.


	for(uint8_t level = 0; level < transform_levels; ++level) {
		uint32_t current_width = (uint32_t) data_width >> level;
		uint32_t current_height = (uint32_t) data_height >> level;


		//Horizontal
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
