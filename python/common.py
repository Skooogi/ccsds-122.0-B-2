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

    def get_bmax(self):
        temp = -1
        temp = max(temp, self.get_dmax(0))
        temp = max(temp, self.get_dmax(1))
        temp = max(temp, self.get_dmax(2))
        return temp

    def get_dmax(self, family):
        temp = -1
        for i in range(20):
            if self.get_status(21*family+1+i) == 0:
                temp = 0
            elif self.get_status(21*family+1+i) == 1:
                return 1
        return temp

    def get_gmax(self, family):
        temp = -1
        for i in range(16):
            if self.get_status(21*family+5+i) == 0:
                temp = 0
            elif self.get_status(21*family+5+i) == 1:
                return 1
        return temp

    def get_status(self, i):
        temp = (((self.status1 >> i) & 1) << 1) | ((self.status2 >> i) & 1)
        return temp if temp < 3 else -1

    def set_status(self, ac_index, value):
        temp = 3 if value == -1 else value

        reset = ~(1 << ac_index)
        self.status1 &= reset
        self.status2 &= reset

        self.status1 |= ((temp >> 1) & 1) << ac_index
        self.status2 |= (temp & 1) << ac_index

    def __str__(self):
        output = 'BLOCK:\nDC\t' + format(int(self.dc),'04d')+'\n'
        output += f'bitDC\t{self.bitAC}\nbitAC\t{self.bitAC}\n'
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

