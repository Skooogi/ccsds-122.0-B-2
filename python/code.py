import numpy as np
import math
import bitstream
import run_length_encoding as rle

from dataclasses import dataclass

@dataclass
class Block:
    bitAC: int
    dc: int
    status1: np.ulonglong
    status2: np.ulonglong
    tran_p: int
    tran_b: int
    tran_d: int
    tran_g: int
    bmax: int
    dmax: np.ndarray = np.zeros(3, dtype='int')
    tran_h: np.ndarray = np.zeros(3, dtype='int')
    ac: np.ndarray = np.zeros(63)

def select_coding(delta, J, N):

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

def twos(value, bits):
    if(value & 1 << (bits - 1)):
        return ~value + 1
    
    return value

def split_coding(diffs, first, size, N):

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
        bitstream.out(k, math.ceil(math.log(N,2)))
        if(i == 0):
            bitstream.out(first, 8)

        for j in range(1 if i==0 else 0,16):
            index = i*16+j
            if index >= size:
                break
            z = int(diffs[index]/pow(2,k))
            bitstream.out(0, z)
            bitstream.out(1, 1)
        if(k != 0):
            for j in range(1 if i == 0 else 0,16):
                index = i*16+j
                if index >= size:
                    break
                bitstream.out(diffs[index] & ((1 << k) -1), k)

def encode_dc_magnitudes(blocks, bitDC, q):

    #DC coding
    N = max(bitDC - q, 1)
    quantized = np.zeros(len(blocks))

    #print("Coding DC coefficients with:\n[bitDC]\t", bitDC, "\n[q]\t", q, "\n[N]\t", N)
    
    if(N == 1):
        quantized[0] = int(blocks[0].dc / pow(2,q))
        temp = int(quantized[0])
        j = 1

        for i in range(1,len(blocks)):
            if(j == 7):
                j = 1
                temp = 0
            temp <<= 1
            j += 1
            quantized[i] = int(blocks[i].dc / pow(2,q))
            temp |= int(quantized[i])
        return
        
    #First DC coefficient is uncoded
    diffs = np.zeros(len(blocks), dtype='int')
    for i in range(len(blocks)):
        blocks[i].dc = twos(blocks[i].dc, bitDC)
    
    last = int(blocks[0].dc / pow(2, q))
    first = int(last)

    #Rest of the DC coefficients
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
    print("Coding AC coefficients with:\n[bitAC]\t", bitACGlobal, "\n[q]\t", q, "\n[N]\t", N)

    if(N == 1):
        quantized[0] = int(blocks[0])
        temp = int(quantized[0])
        j = 1

        print("AC")
        for i in range(1,len(blocks)):
            if(j == 7):
                print(temp, end='')
                j = 1
                temp = 0
            temp <<= 1
            j += 1
            quantized[i] = int(blocks[i])
            temp |= int(quantized[i])
        return
             
    diffs = np.zeros(len(blocks), dtype='int')

    last = abs(blocks[0].bitAC)
    first = last
    diffs[0] = first
    
    #Rest of the AC coefficients
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

def subband_lim(j, b):

    if(j == 0 or j == 21) and b < 3:
        return True
    elif((1 <= j <= 4) or (22 <= j <= 25) or j == 42) and b < 2:
        return True
    elif((5 <= j <= 20) or (26 <= j <= 41) or (43 <= j <= 46)) and b < 1:
        return True
    else:
        return False

"""

    00 = 0
    01 = 1
    10 = 2
    11 = -1

"""

def status_to_int(block, i):
    temp = (((block.status1 >> i) & 1) << 1) | ((block.status2 >> i) & 1)
    return temp if temp < 3 else -1

def int_to_status(block, i, temp):
    val = 3 if temp == -1 else temp

    block.status1 |= ((val >> 1) & 1) << i
    block.status2 |= (val & 1) << i

def stage_0(blocks, q, b):

    for i in range(len(blocks)):
        if(3 <= b < q):
            bitstream.out((blocks[i].dc >> b) & 1, 1)

def stage_1(blocks, b):

    for i in range(len(blocks)):
    
        if(blocks[i].bitAC < b):
            continue

        #Initialization
        blocks[i].status1 = 0
        blocks[i].status2 = 0

        for j in range(63):
            if(subband_lim(j, b)):
                int_to_status(blocks[i], j, -1)
            elif(abs(blocks[i].ac[j]) < pow(2,b)):
                int_to_status(blocks[i], j, 0)
            elif(pow(2,b) <= abs(blocks[i].ac[j]) < pow(2,b+1)):
                int_to_status(blocks[i], j, 1)
            elif(pow(2,b+1) <= abs(blocks[i].ac[j])):
                int_to_status(blocks[i], j, 2)
            #print(b,status_to_int(blocks[i], j), j)
        #print()
        
        #types_p and signs_p
        types_p = 0
        signs_p = 0
        size_s = 0
        size_p = 0

        #print(status_to_int(blocks[i], 0),status_to_int(blocks[i], 21),status_to_int(blocks[i], 42))

        if(0 <= status_to_int(blocks[i], 0) <= 1):
            types_p |= (abs(blocks[i].ac[0]) >> b) & 1
            size_p += 1

            if(status_to_int(blocks[i], 0) == 1):
                signs_p |= 1 if blocks[i].ac[0] < 0 else 0
                size_s += 1

        if(0 <= status_to_int(blocks[i], 21) <= 1):
            types_p <<= 1
            types_p |= (abs(blocks[i].ac[21]) >> b) & 1
            size_p += 1

            if(status_to_int(blocks[i], 21) == 1):
                signs_p <<= 1
                signs_p |= 1 if blocks[i].ac[21] < 0 else 0
                size_s += 1

        if(0 <= status_to_int(blocks[i], 42) <= 1):
            types_p <<= 1
            types_p |= (abs(blocks[i].ac[42]) >> b) & 1
            size_p += 1

            if(status_to_int(blocks[i], 42) == 1):
                signs_p <<= 1
                signs_p |= 1 if blocks[i].ac[42] < 0 else 0
                size_s += 1

        if(size_p > 0):
            #if(b == 2):
                #print(format(blocks[i].tran_p, '03b'), status_to_int(blocks[i], 0), status_to_int(blocks[i], 21), status_to_int(blocks[i], 42))
            bitstream.code(types_p, size_p, 0)
            if(size_s > 0):
                bitstream.code(signs_p, size_s, 0, -1)
  

def stage_2(blocks, b):

    for i in range(len(blocks)):
    
        if(blocks[i].bitAC < b):
            continue

        #TRANB
        blocks[i].bmax = -2
        for j in range(1,63):
            if(j == 21 or j == 42):
                continue
            blocks[i].bmax = max(blocks[i].bmax, status_to_int(blocks[i], j))

        if(blocks[i].tran_b != 1):
            blocks[i].tran_b = blocks[i].bmax
            #print("[",i,"]","B",tmax)
            bitstream.code(blocks[i].bmax, 1, 0)

        #TRAND
        dmax = [[-1,-1],[-1,-1],[-1,-1]]
        tran_d = 0
        if(blocks[i].tran_b != 0 and blocks[i].bmax != -1):
            size = 0
            for j in range(20):

                dmax[0][0] = max(dmax[0][0], status_to_int(blocks[i], 1+j))
                if(0 <= status_to_int(blocks[i], 1+j) <= 1):
                    dmax[0][1] = max(dmax[0][1], status_to_int(blocks[i], 1+j))

                dmax[1][0] = max(dmax[1][0], status_to_int(blocks[i], 22+j))
                if(0 <= status_to_int(blocks[i], 22+j) <= 1):
                    dmax[1][1] = max(dmax[1][1], status_to_int(blocks[i], 22+j))

                dmax[2][0] = max(dmax[2][0], status_to_int(blocks[i], 43+j))
                if(0 <= status_to_int(blocks[i], 43+j) <= 1):
                    dmax[2][1] = max(dmax[2][1], status_to_int(blocks[i], 43+j))

            if((blocks[i].dmax[0]) != 1 and 0 <= dmax[0][1] <= 1):
                tran_d |= dmax[0][1]
                size += 1

            if((blocks[i].dmax[1]) != 1 and 0 <= dmax[1][1] <= 1):
                tran_d <<= 1
                tran_d |= dmax[1][1]
                size += 1

            if((blocks[i].dmax[2]) != 1 and 0 <= dmax[2][1] <= 1):
                tran_d <<= 1
                tran_d |= dmax[2][1]
                size += 1

            blocks[i].dmax[0] = max(blocks[i].dmax[0], dmax[0][1])
            blocks[i].dmax[1] = max(blocks[i].dmax[1], dmax[1][1])
            blocks[i].dmax[2] = max(blocks[i].dmax[2], dmax[2][1])
            if(size != 0):
                #print("[",b,"]","D",bin(tran_d)[2:], size)
                bitstream.code(tran_d, size, 1)
        
        #types_c and signs_c
        for ci in range(3):
            if(blocks[i].dmax[ci] <= 0):
                continue
            types_c = 0
            signs_c = 0
            size_s = 0
            size_c = 0
            for cj in range(4):
                index = 1+ci*21+cj
                if(0 <= status_to_int(blocks[i], index) <= 1):
                    types_c <<= 1
                    size_c += 1
                    types_c |= status_to_int(blocks[i], index)
                    if(types_c & 1):
                        signs_c <<= 1
                        size_s += 1
                        signs_c |= 1 if blocks[i].ac[index] < 0 else 0
                    #print(blocks[i].ac[index],index)
            if(size_c != 0):
                #print("C",bin(types_c)[2:], size_c, bin(signs_c)[2:], size_s)
                bitstream.code(types_c, size_c, 0)
                if(size_s != 0):
                    bitstream.out(signs_c, size_s)

def stage_3(blocks, b):

    for i in range(len(blocks)):
        if(blocks[i].tran_b == 0 or blocks[i].bmax == -1):
            continue
    
        if(blocks[i].bitAC < b):
            continue

        #TRANG
        gmax = [[-2,-2], [-2,-2], [-2,-2]]
        size = 0
        tran_g = 0
        for j in range(16):
            gmax[0][0] = max(gmax[0][0], status_to_int(blocks[i], 5+j))
            if(0 <= status_to_int(blocks[i], 5+j) <= 1):
                gmax[0][1] = max(gmax[0][0], status_to_int(blocks[i], 5+j))

            gmax[1][0] = max(gmax[1][0], status_to_int(blocks[i], 26+j))
            if(0 <= status_to_int(blocks[i], 26+j) <= 1):
                gmax[1][1] = max(gmax[1][0], status_to_int(blocks[i], 26+j))

            gmax[2][0] = max(gmax[2][0], status_to_int(blocks[i], 47+j))
            if(0 <= status_to_int(blocks[i], 47+j) <= 1):
                gmax[2][1] = max(gmax[2][0], status_to_int(blocks[i], 47+j))

        if((blocks[i].dmax[0]) > 0 and 0 <= gmax[0][1] <= 1):
            blocks[i].tran_g |= gmax[0][1]
            tran_g |= gmax[0][1]
            size += 1

        if((blocks[i].dmax[1]) > 0 and 0 <= gmax[1][1] <= 1):
            blocks[i].tran_g <<= 1
            blocks[i].tran_g |= gmax[1][1]
            tran_g <<= 1
            tran_g |= gmax[1][1]
            size += 1

        if((blocks[i].dmax[2]) > 0 and 0 <= gmax[2][1] <= 1):
            blocks[i].tran_g <<= 1
            blocks[i].tran_g |= gmax[2][1]
            tran_g <<= 1
            tran_g |= gmax[2][1]
            size += 1
        
        if(size != 0):
            #print("[",i,"]","G",bin(tran_g)[2:], size)
            bitstream.code(tran_g, size, 0)

        #TRANH
        hmax = np.ones(12, dtype='int')*-2
        for hi in range(3):
            if(gmax[hi][1] <= 0):
                continue

            for hj in range(4):
                for j in range(4):
                    index = 5+hi*21+hj*4+j
                    #print(status_to_int(blocks[i], index), end=' ')
                    hmax[hi*4+hj] = max(hmax[hi*4+hj], status_to_int(blocks[i],index))
                #print()
                        

            temp = ''.join(map(str, hmax[hi*4:hi*4+4])).replace("-2",'').replace("2",'')
            #print("[",i,"]","H", temp, hi)
            if(len(temp) != 0):
                bitstream.code(int(temp, 2), len(temp), 0 if len(temp) < 4 else 1)

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
                    if(0 <= status_to_int(blocks[i], index) <= 1):
                        types_h <<= 1
                        size_h += 1
                        types_h |= ((abs(blocks[i].ac[index]) >> b) & 1)
                        if(types_h & 1):
                            signs_h <<= 1
                            signs_h |= 1 if blocks[i].ac[index] < 0 else 0
                            size_s += 1
                if(size_h > 0):
                    #print("H",bin(types_h)[2:],size_h, bin(signs_h)[2:], size_s)
                    bitstream.code(types_h, size_h, 0 if size_h < 4 else 1)
                    if(size_s > 0):
                        bitstream.out(signs_h, size_s)

def stage_4(blocks, b):

    bitstring = ""

    for i in range(len(blocks)):

        if(blocks[i].bitAC < b):
            continue

        for pi in range(3):
            index = pi * 21
            if(status_to_int(blocks[i], index) == 2):
                bitstring += str((abs(blocks[i].ac[index]) >> b) & 1)

        for ci in range(3):
            for j in range(4):
                index = 1 + ci*21 + j
                if(status_to_int(blocks[i], index) == 2):
                    bitstring += str((abs(blocks[i].ac[index]) >> b) & 1)

        for hi in range(3):
            for hj in range(4):
                for j in range(4):
                    index = 5+hi*21+hj*4+j
                    if(status_to_int(blocks[i], index) == 2):
                        bitstring += str((abs(blocks[i].ac[index]) >> b) & 1)

    if(len(bitstring) > 0):
        #bitstream.out_bits(rle.compress(bitstring))
        bitstream.out_bits(bitstring)
