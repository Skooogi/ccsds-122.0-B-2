import numpy as np

#Collection of frequently used functions and classes

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
        self.ac         = np.zeros(63, dtype=int)

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

    def __str__(self):
        #TODO: print in correct raster order
        output = '| ' + format(int(self.dc),'04d')
        for i in range(63):
            output += ' ' + format(int(self.ac[i]),'04d')
            if((i + 2) % 8 == 0):
                output += ' |\n|'
        return output[:-2]


def status_to_int(block, i):
    temp = (((block.status1 >> i) & 1) << 1) | ((block.status2 >> i) & 1)
    return temp if temp < 3 else -1

def int_to_status(block, i, temp):
    val = 3 if temp == -1 else temp

    block.status1 |= ((val >> 1) & 1) << i
    block.status2 |= (val & 1) << i


def subband_lim(ac_index, current_bitplane):

    # Checks whether or not ac coefficient scaling means 
    # bitplane is necessarily 0 and is not encoded
    # Figure 3-4

    if(ac_index == 0 or ac_index == 21) and current_bitplane < 3:
        return True
    elif((1 <= ac_index <= 4) or (22 <= ac_index <= 25) or ac_index == 42) and current_bitplane < 2:
        return True
    elif((5 <= ac_index <= 20) or (26 <= ac_index <= 41) or (43 <= ac_index <= 46)) and current_bitplane < 1:
        return True
    else:
        return False

def twos_complement(value, bits):
    if(value & 1 << (bits - 1)):
        return ~value + 1
    
    return value

def pad_image_size(data, width, height):
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

