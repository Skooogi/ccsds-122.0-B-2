import numpy as np
import math
import word_mapping
import file_io
import run_length_encoding as rle
from common import twos_complement, subband_lim

def select_coding(delta, J, N):
    #Heuristic way of selecting coding option k as in figure 4-10

    if(64*delta > 23*J*pow(2, N)):
        return -1
    elif(207*J > 128*delta):
        return 0
    elif(J*pow(2,N+5) <= 128*delta + 49*J):
        return N-2
    else:
        k = 1
        while(J*pow(2,k+7) <= 128*delta + 49):
            k += 1
        return k

def split_coding(diffs, first, size, N):

    #Encodes the given values in 'diffs' with
    #value/(2^k) zeros followed by a 1 and k least significant bits of value
    #4.3.2.9

    for i in range(0, int(size/16)+1):
        gaggle_sum = 0
        for j in range(1 if i == 0 else 0,16):
            index = i*16+j
            if index >= size:
                break
            gaggle_sum += diffs[index]

        J = 16
        if(i == 0):
            J -= 1

        k = select_coding(gaggle_sum, J, N)
        file_io.out(k, math.ceil(math.log(N,2)))
        if(i == 0):
            file_io.out(first, 8)

        for j in range(1 if i==0 else 0,16):
            index = i*16+j
            if index >= size:
                break
            z = int(diffs[index]/pow(2,k))
            file_io.out(0, z)
            file_io.out(1, 1)
        if(k != 0):
            for j in range(1 if i == 0 else 0,16):
                index = i*16+j
                if index >= size:
                    break
                file_io.out(diffs[index] & ((1 << k) -1), k)

def encode_dc_initial(blocks, bitDC, q):


    #DC coding
    N = max(bitDC - q, 1)
    quantized = np.zeros(len(blocks))

    if(N == 1):
        #Coefficients are 1 bit long and no further coding is required
        temp = int(blocks[0].dc / pow(2, q))
        j = 1

        for i in range(1,len(blocks)):
            if(j == 7):
                j = 0
                file_io.out(temp, 8)
                temp = 0
            temp <<= 1
            j += 1
            temp = int(blocks[i].dc / pow(2, q))
        return
        
    #First DC coefficient is uncoded
    diffs = np.zeros(len(blocks), dtype='int')
    for i in range(len(blocks)):
        blocks[i].dc = twos_complement(blocks[i].dc, bitDC)
    
    last = int(blocks[0].dc / pow(2, q))
    first = int(last)

    #Rest of the DC coefficients
    #4.3.2.4
    for i in range(1, len(blocks)):

        sigma = int(blocks[i].dc / pow(2, q)) - last
        theta = min(last + pow(2, (N-1)), pow(2, (N-1)) - 1 - last)
        last = int(blocks[i].dc / pow(2, q))
        res = 0

        if sigma >= 0 and sigma <= theta:
            res = 2*sigma
        elif sigma < 0 and sigma >= -theta:
            res = -2*sigma-1
        else:
            res = theta + abs(sigma)
        
        diffs[i] = res

    split_coding(diffs, first, len(blocks), N)

def encode_ac_magnitudes(blocks, bitACGlobal, q):

    N = int(abs(math.log(1 + bitACGlobal,2)) + 1)

    if(N == 1):
        #Coefficients are 1 bit long and no further coding is required
        temp = int(blocks[0].bitAC)
        j = 1

        for i in range(1,len(blocks)):
            if(j == 7):
                file_io.out(temp, 8)
                j = 0
                temp = 0
            temp <<= 1
            j += 1
            temp |= blocks[i].bitAC
        return
             
    diffs = np.zeros(len(blocks), dtype='int')

    last = abs(blocks[0].bitAC)
    first = last
    diffs[0] = first
    
    #Rest of the AC coefficients
    #4.3.2.4
    for i in range(1, len(blocks)):
        sigma = abs(blocks[i].bitAC) - last
        theta = min(last, pow(2,N) - 1 - last)
        last = abs(blocks[i].bitAC)
        res = 0

        if sigma >= 0 and sigma <= theta:
            res = 2*sigma
        elif sigma < 0 and sigma >= -theta:
            res = 2*abs(sigma)-1
        else:
            res = theta + abs(sigma)
        diffs[i] = int(res)

    split_coding(diffs, first, len(blocks), N)


def stage_0(blocks, q, b):

    #Any remaining DC bits
    for i in range(len(blocks)):
        if(3 <= b < q):
            word_mapping.code((blocks[i].dc >> b) & 1, 1, 0)

#NOTE: Stages 1 to 3 are not optimal and should be simplified
#They follow steps given in section 4.5.3
def stage_1(blocks, b):

    for i in range(len(blocks)):
    
        if(blocks[i].bitAC < b):
            continue

        #Set each coefficient state
        blocks[i].status1 = 0
        blocks[i].status2 = 0

        for j in range(63):
            if(subband_lim(j, b)):
                blocks[i].set_status(j, -1)
            elif(abs(blocks[i].ac[j]) < pow(2,b)):
                blocks[i].set_status(j, 0)
            elif(pow(2,b) <= abs(blocks[i].ac[j]) < pow(2,b+1)):
                blocks[i].set_status(j, 1)
            elif(pow(2,b+1) <= abs(blocks[i].ac[j])):
                blocks[i].set_status(j, 2)
        
        #types_p and signs_p
        types_p = 0
        signs_p = 0
        size_s = 0
        size_p = 0

        if(0 <= blocks[i].get_status(0) <= 1):
            types_p |= (abs(blocks[i].ac[0]) >> b) & 1
            size_p += 1

            if(blocks[i].get_status(0) == 1):
                signs_p |= 1 if blocks[i].ac[0] < 0 else 0
                size_s += 1

        if(0 <= blocks[i].get_status(21) <= 1):
            types_p <<= 1
            types_p |= (abs(blocks[i].ac[21]) >> b) & 1
            size_p += 1

            if(blocks[i].get_status(21) == 1):
                signs_p <<= 1
                signs_p |= 1 if blocks[i].ac[21] < 0 else 0
                size_s += 1

        if(0 <= blocks[i].get_status(42) <= 1):
            types_p <<= 1
            types_p |= (abs(blocks[i].ac[42]) >> b) & 1
            size_p += 1

            if(blocks[i].get_status(42) == 1):
                signs_p <<= 1
                signs_p |= 1 if blocks[i].ac[42] < 0 else 0
                size_s += 1

        if(size_p > 0):
            word_mapping.code(types_p, size_p, 0)
            if(size_s > 0):
                word_mapping.code(signs_p, size_s, 0, -1)
  

def stage_2(blocks, b):

    for i in range(len(blocks)):
    
        if(blocks[i].bitAC < b):
            continue

        #TRANB
        bmax = blocks[i].get_bmax()

        if(blocks[i].tran_b != 1 and bmax >= 0):
            blocks[i].tran_b = bmax
            word_mapping.code(blocks[i].tran_b, 1, 0)

        #TRAND
        if(blocks[i].tran_b != 0 and bmax != -1):
            tran_d = 0
            size = 0

            status_f0 = blocks[i].get_dmax(0)
            status_f1 = blocks[i].get_dmax(1)
            status_f2 = blocks[i].get_dmax(2)
            
            subband_mask = 0
            subband_mask |= 4 if blocks[i].get_dmax(0) == -1 else 0
            subband_mask |= 2 if blocks[i].get_dmax(1) == -1 else 0
            subband_mask |= 1 if blocks[i].get_dmax(2) == -1 else 0

            blocks[i].tran_d |= subband_mask

            if(blocks[i].tran_d & 4 != 4 and status_f0 >= 0):
                tran_d |= status_f0
                blocks[i].tran_d |= 4*status_f0
                size += 1

            if(blocks[i].tran_d & 2 != 2 and status_f1 >= 0):
                tran_d <<= 1
                tran_d |= status_f1
                blocks[i].tran_d |= 2*status_f1
                size += 1

            if(blocks[i].tran_d & 1 != 1 and status_f2 >= 0):
                tran_d <<= 1
                tran_d |= status_f2
                blocks[i].tran_d |= status_f2
                size += 1
            
            if(size != 0):
                word_mapping.code(tran_d, size, 1 if size == 3 else 0)

        """
        dmax = [[-1,-1],[-1,-1],[-1,-1]]
        tran_d = 0
        if(blocks[i].tran_b != 0 and blocks[i].bmax != -1):
            size = 0
            for j in range(20):

                dmax[0][0] = max(dmax[0][0], blocks[i].get_status(1+j))
                if(0 <= blocks[i].get_status(1+j) <= 1):
                    dmax[0][1] = max(dmax[0][1], blocks[i].get_status(1+j))

                dmax[1][0] = max(dmax[1][0], blocks[i].get_status(22+j))
                if(0 <= blocks[i].get_status(22+j) <= 1):
                    dmax[1][1] = max(dmax[1][1], blocks[i].get_status(22+j))

                dmax[2][0] = max(dmax[2][0], blocks[i].get_status(43+j))
                if(0 <= blocks[i].get_status(43+j) <= 1):
                    dmax[2][1] = max(dmax[2][1], blocks[i].get_status(43+j))

            if((blocks[i].dmax[0]) != 1 and 0 <= dmax[0][1] <= 1):
                tran_d |= dmax[0][1]
                blocks[i].tran_d |= 4 * dmax[0][1]
                size += 1

            if((blocks[i].dmax[1]) != 1 and 0 <= dmax[1][1] <= 1):
                tran_d <<= 1
                blocks[i].tran_d |= 2 * dmax[1][1]
                tran_d |= dmax[1][1]
                size += 1

            if((blocks[i].dmax[2]) != 1 and 0 <= dmax[2][1] <= 1):
                tran_d <<= 1
                tran_d |= dmax[2][1]
                blocks[i].tran_d |= 1 * dmax[2][1]
                size += 1

            blocks[i].dmax[0] = max(blocks[i].dmax[0], dmax[0][1])
            blocks[i].dmax[1] = max(blocks[i].dmax[1], dmax[1][1])
            blocks[i].dmax[2] = max(blocks[i].dmax[2], dmax[2][1])

            if(size != 0):
                word_mapping.code(tran_d, size, 1 if size == 3 else 0)
        """
        #types_c and signs_c
        for ci in range(3):
            if(blocks[i].tran_d >> (2-ci) & 1 != 1):
                continue
            types_c = 0
            signs_c = 0
            size_s = 0
            size_c = 0
            for cj in range(4):
                index = 1+ci*21+cj
                if(0 <= blocks[i].get_status(index) <= 1):
                    types_c <<= 1
                    size_c += 1
                    types_c |= blocks[i].get_status(index)
                    if(types_c & 1):
                        signs_c <<= 1
                        size_s += 1
                        signs_c |= 1 if blocks[i].ac[index] < 0 else 0
            if(size_c != 0):
                word_mapping.code(types_c, size_c, 0)
                if(size_s != 0):
                    word_mapping.code(signs_c, size_s, 0, -1)

def stage_3(blocks, b):

    for i in range(len(blocks)):
        if(blocks[i].tran_b == 0 or blocks[i].bmax == -1):
            continue
    
        if(blocks[i].bitAC < b):
            continue

        #TRANG
        size = 0
        tran_g = 0

        if blocks[i].dmax[0] == 1 and blocks[i].tran_g & 4 == 0:
            blocks[i].tran_g |= 4 * blocks[i].get_gmax(0)
            tran_g |= blocks[i].get_gmax(0)
            size += 1

        if blocks[i].dmax[1] == 1 and blocks[i].tran_g & 2 == 0:
            blocks[i].tran_g |= 2 * blocks[i].get_gmax(1)
            tran_g <<= 1
            tran_g |= blocks[i].get_gmax(1)
            size += 1

        if blocks[i].dmax[2] == 1 and blocks[i].tran_g & 1 == 0:
            blocks[i].tran_g |= 1 * blocks[i].get_gmax(2)
            tran_g <<= 1
            tran_g |= blocks[i].get_gmax(2)
            size += 1

        if(size != 0):
            word_mapping.code(tran_g, size, 0)

        #TRANH
        hmax = np.ones(12, dtype='int')*-2
        for hi in range(3):
            if(blocks[i].get_gmax(hi) <= 0):
                continue

            for hj in range(4):
                for j in range(4):
                    index = 5+hi*21+hj*4+j
                    hmax[hi*4+hj] = max(hmax[hi*4+hj], blocks[i].get_status(index))

            temp = ''.join(map(str, hmax[hi*4:hi*4+4])).replace("-2",'').replace("2",'')
            if(len(temp) != 0):
                print(i, hi, temp)
                word_mapping.code(int(temp, 2), len(temp), 0 if len(temp) < 4 else 1)

        continue
        #types_h and signs_h
        for hi in range(3):
            if(gmax[hi][1] != 1):
                continue

            for hj in range(4):
                if(hmax[hi*4+hj] != 1):
                    continue

                size_h = 0
                size_s = 0
                types_h = 0
                signs_h = 0
                for j in range(4):
                    index = 5+hi*21+hj*4+j
                    if(0 <= blocks[i].get_status(index) <= 1):
                        types_h <<= 1
                        size_h += 1
                        types_h |= ((abs(blocks[i].ac[index]) >> b) & 1)
                        if(types_h & 1):
                            signs_h <<= 1
                            signs_h |= 1 if blocks[i].ac[index] < 0 else 0
                            size_s += 1
                if(size_h > 0):
                    word_mapping.code(types_h, size_h, 0 if size_h < 4 else 1)
                    if(size_s > 0):
                        word_mapping.code(signs_h, size_s, 0, -1)

def stage_4(blocks, b):
    #Adds all bits of bitplane b from coefficients of type 2
    bitstring = ""

    for i in range(len(blocks)):

        if(blocks[i].bitAC < b):
            continue

        for pi in range(3):
            index = pi * 21
            if(blocks[i].get_status(index) == 2):
                bitstring += str((abs(blocks[i].ac[index]) >> b) & 1)

        for ci in range(3):
            for j in range(4):
                index = 1 + ci*21 + j
                if(blocks[i].get_status(index) == 2):
                    bitstring += str((abs(blocks[i].ac[index]) >> b) & 1)

        continue
        for hi in range(3):
            for hj in range(4):
                for j in range(4):
                    index = 5+hi*21+hj*4+j
                    if(blocks[i].get_status(index) == 2):
                        bitstring += str((abs(blocks[i].ac[index]) >> b) & 1)

    if(len(bitstring) > 0):
        print("4:"+bitstring)
        file_io.out_bits(bitstring)
