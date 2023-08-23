import numpy as np
import math

#Collection of frequently used functions and classes

state_map = [0,1,2,-1]
state_map_inv_1 = [0,0,1,1]
state_map_inv_2 = [0,1,0,1]
mask_64 = 0xffffffffffffffff
b_mask = 0x7ffffbffffdffffe
d_mask = 0x1ffffe
g_mask = 0x1fffe0
h_mask = 0x1e0

class Block(object):
    # https://public.ccsds.org/Pubs/122x0b2.pdf section 4.1
    # NOTE:Currently uses more memory than necessary for recording debugging data
    #
    # Holds the DC and AC coefficients for a single block,
    # as well as general information of the current state for encoding.
    # Only 16 blocks(1 gaggle) need to be allocated concurrently.
    def __init__(self):
        self.bitAC      = 0 #5 bit uint
        self.dc         = 0
        self.ac         = np.zeros(63, dtype='int32')

        #The rest is used in encoding stages 4.5.3.1.7
        self.status1    = 0 #64 bit uint
        self.status2    = 0 #64 bit uint
        self.tran_b     = 0 #1 bit
        self.tran_p     = 0 #3 bit uint
        self.tran_d     = 0 #3 bit uint
        self.tran_g     = 0 #3 bit uint
        self.tran_h     = np.zeros(3, dtype=int)
        self.bmax       = 0 #1 bit
        self.dmax       = np.ones(3, dtype=int)

    def get_bmax(self):
        filtered = (~self.status1 & self.status2) & b_mask
        return int(filtered > 0)

    def get_dmax(self, family):
        filtered = (~self.status1 & self.status2)
        return int(filtered >> 21*family & d_mask > 0)

    def get_gmax(self, family):
        filtered = (~self.status1 & self.status2)
        return int(filtered >> 21*family & g_mask > 0)

    def get_hmax(self, family, quarter):
        filtered = (~self.status1 & self.status2)
        return int(filtered >> (21*family + quarter * 4) & h_mask > 0)

    def get_status(self, i):
        return state_map[(self.status1 >> i & 1) * 2 + (self.status2 >> i & 1)]

    def set_status(self, ac_index, value):

        self.status1 = (self.status1 & ~(1 << ac_index)) | (state_map_inv_1[value] << ac_index)
        self.status2 = (self.status2 & ~(1 << ac_index)) | (state_map_inv_2[value] << ac_index)
        #self.status1 ^= (-state_map_inv_1[value] ^ self.status1) & (1 << ac_index)
        #self.status2 ^= (-state_map_inv_2[value] ^ self.status2) & (1 << ac_index)

    def set_status_with(self, status1, status2):
        self.status1 = status1
        self.status2 = status2

    def __str__(self):
        output = 'BLOCK:\nDC\t' + format(int(self.dc),'04d')+'\n'
        output += f'bitDC\t{self.bitAC}\nbitAC\t{self.bitAC}\n'
        output += f'bmax\t{self.get_bmax()}\n'
        for family in range(3):
            output += 'Family '+str(family) + '\n'
            output += '\tp\t' + format(self.ac[family*21+0], '04d')
            output += '\t\t    |' + format(self.get_status(family*21+0), '02d') + '\n'
            output += '\tc\t' + format(self.ac[family*21+1], '04d')
            output += ' ' + format(self.ac[family*21+2], '04d')
            output += ' ' + format(self.ac[family*21+3], '04d')
            output += ' ' + format(self.ac[family*21+4], '04d')
            output += ' |' + format(self.get_status(family*21+1), '02d')
            output += ' ' + format(self.get_status(family*21+2), '02d')
            output += ' ' + format(self.get_status(family*21+3), '02d')
            output += ' ' + format(self.get_status(family*21+4), '02d') + '\n'

            output += f'\tH{family}0\t' + format(self.ac[family*21+5], '04d')
            output += ' ' + format(self.ac[family*21+6], '04d')
            output += ' ' + format(self.ac[family*21+7], '04d')
            output += ' ' + format(self.ac[family*21+8], '04d')
            output += ' |' + format(self.get_status(family*21+5), '02d')
            output += ' ' + format(self.get_status(family*21+6), '02d')
            output += ' ' + format(self.get_status(family*21+7), '02d')
            output += ' ' + format(self.get_status(family*21+8), '02d') + '\n'

            output += f'\tH{family}1\t' + format(self.ac[family*21+9], '04d')
            output += ' ' + format(self.ac[family*21+10], '04d')
            output += ' ' + format(self.ac[family*21+11], '04d')
            output += ' ' + format(self.ac[family*21+12], '04d')
            output += ' |' + format(self.get_status(family*21+9), '02d')
            output += ' ' + format(self.get_status(family*21+10), '02d')
            output += ' ' + format(self.get_status(family*21+11), '02d')
            output += ' ' + format(self.get_status(family*21+12), '02d') + '\n'

            output += f'\tH{family}2\t' + format(self.ac[family*21+13], '04d')
            output += ' ' + format(self.ac[family*21+14], '04d')
            output += ' ' + format(self.ac[family*21+15], '04d')
            output += ' ' + format(self.ac[family*21+16], '04d')
            output += ' |' + format(self.get_status(family*21+13), '02d')
            output += ' ' + format(self.get_status(family*21+14), '02d')
            output += ' ' + format(self.get_status(family*21+15), '02d')
            output += ' ' + format(self.get_status(family*21+16), '02d') + '\n'

            output += f'\tH{family}3\t' + format(self.ac[family*21+17], '04d')
            output += ' ' + format(self.ac[family*21+18], '04d')
            output += ' ' + format(self.ac[family*21+19], '04d')
            output += ' ' + format(self.ac[family*21+20], '04d')
            output += ' |' + format(self.get_status(family*21+17), '02d')
            output += ' ' + format(self.get_status(family*21+18), '02d')
            output += ' ' + format(self.get_status(family*21+19), '02d')
            output += ' ' + format(self.get_status(family*21+20), '02d') + '\n'

        return output




subband_bitplane_2 = 0x200001
subband_bitplane_1 = 0x040003c0001e
subband_bitplane_0 = 0x7bfffc1fffe0

sub_map_2 = np.array([1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
sub_map_1 = np.array([1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
sub_map_0 = np.array([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])

sub_map = [sub_map_0, sub_map_1, sub_map_2]

def subband_lim(ac_index, current_bitplane):

    # Checks whether or not ac coefficient scaling means 
    # bitplane is necessarily 0 and is not encoded
    # Figure 3-4
    if(current_bitplane > 2):
        return False

    return sub_map[current_bitplane][ac_index]

def twos_complement(value, bits):
    if(value & 1 << (bits - 1)):
        return ~abs(value) + 1 & (2**bits - 1)
    
    return value

def pad_data_to_8(data, width, height):
    #Pad image width and height to multiples of 8

    pad_width = 8 - width % 8
    pad_height = 8 - height % 8

    pad_width = 0 if pad_width == 8 else pad_width
    pad_height = 0 if pad_height == 8 else pad_height

    if 0 < pad_width < 8:
        last_column = data[:,width - 1]
        last_column = last_column.reshape(height, 1)
        for i in range(pad_width):
            data = np.hstack((data, last_column))

    if 0 < pad_height < 8:
        last_row = data[height - 1, :]
        last_row = last_row.reshape(1, width+pad_width)
        for i in range(pad_height):
            data = np.vstack((data, last_row))

    return data, pad_width, pad_height


def MSE(data_in, data_out, width, height):
    n = height * width
    # MSE
    mean_squared_error = 0
    for i in range(height):
        for j in range(width):
            temp = data_out[i, j] - data_in[i, j]
            temp = temp * temp
            mean_squared_error += temp
    mean_squared_error /= n
    return mean_squared_error
 

def PSNR(mean_squared_error, bitdepth):

    peak_signal_to_noise_ratio = math.inf
    if (mean_squared_error != 0):
        peak_signal_to_noise_ratio = 10*math.log(((2**bitdepth-1)*(2**bitdepth-1))/mean_squared_error, 10)

    print(f'MSE:{mean_squared_error}\nPSNR:{peak_signal_to_noise_ratio} dB')

