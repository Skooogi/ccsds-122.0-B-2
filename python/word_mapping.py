import numpy as np

sym2bit = np.array([0, 2, 1, 3])
sym3bit = np.array([[1, 4, 0, 5, 2, 6, 3, 7], [-1, 3, 0, 4, 1, 5, 2, 6]])
sym4bit = np.array([[10, 1, 3, 6, 2, 5, 9, 12, 0, 8, 7, 13, 4, 14, 11, 15], [-1, 1, 3, 6, 2, 5, 9, 11, 0, 8, 7, 12, 4, 13, 10, 14]])

word2bit = np.array([["1", "01", "001", "000"], 
                          ["00", "01", "10", "11"]])

word3bit = np.array([["1", "01", "001", "00000", "00001", "00010", "000110", "000111"], 
                          ["10", "11", "010", "011", "0010", "0011", "0000", "0001"], 
                          ["000", "001", "010", "011", "100", "101", "110", "111"]])

word4bit = np.array([["1", "01", "001", "0001", "0000000", "0000001", "0000010", "0000011", "00001000", 
                           "00001001", "00001010", "00001011", "00001100", "00001101", "00001110", "00001111"], 
                           ["10", "11", "010", "011", "0010", "0011", "000000", "000001", "000010", 
                            "000011", "000100", "000101", "0001100", "0001101", "0001110", "0001111"], 
                           ["100", "101", "110", "111", "0100", "0101", "0110", "0111", "00100", 
                            "00101", "00110", "00111", "00000", "00001", "00010", "00011"], 
                           ["0000", "0001", "0010", "0011", "0100", "0101", "0110", "0111", 
                            "1000", "1001", "1010", "1011", "1100", "1101", "1110", "1111"]])



words = np.array([], dtype='int')
sizes = np.array([], dtype='int')
symbol_option = np.array([], dtype='int')
options = np.array([[0,0],[0,0,0],[0,0,0,0]], dtype=object)
num = np.zeros(4)
def code(word, word_length, sym_option, uncoded = 1):

    if(word_length == 0):
        raise ValueError("WORD LENGTH 0")

    global num, words, sizes, symbol_option
    
    words = np.append(words, word)
    sizes = np.append(sizes, word_length*uncoded)
    symbol_option = np.append(symbol_option, sym_option)

    if(uncoded < 0):
        return

    if(word_length == 1):
        num[3] += 1
        return

    if(word_length == 2):
        sym = sym2bit[word]
        options[0][0] += len(word2bit[0][sym])
        options[0][1] += len(word2bit[1][sym])

        num[0] += 1
        return

    if(word_length == 3):
        sym = sym3bit[sym_option][word]
        if(sym == -1):
            raise ValueError("SYMBOL ERROR: 000")
        options[1][0] += len(word3bit[0][sym])
        options[1][1] += len(word3bit[1][sym])
        options[1][2] += len(word3bit[2][sym])

        num[1] += 1
        return

    if(word_length == 4):
        sym = sym4bit[sym_option][word]
        if(sym == -1):
            raise ValueError("SYMBOL ERROR: 0000")
        options[2][0] += len(word4bit[0][sym])
        options[2][1] += len(word4bit[1][sym])
        options[2][2] += len(word4bit[2][sym])
        options[2][3] += len(word4bit[3][sym])
        
        num[2] += 1
        return

    print("ENCODING ERROR!")

