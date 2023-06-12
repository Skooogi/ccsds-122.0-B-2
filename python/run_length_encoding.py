import numpy as np
import math
import struct
import sys
import file_io

#Performs basic Huffman coding for data.
#Canonical Huffman tree is used for reduced space required by the coded tree.

class NodeTree(object):

    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def has_left(self):
        return not self.left == None

    def has_right(self):
        return not self.right == None

    def children(self):
        return self.left, self.right

def huffman_code_tree(node, binString=''):

    if type(node) == np.int64:
        return {node: binString}
    (l, r) = node.children()
    d = dict()
    d.update(huffman_code_tree(l, binString + '0'))
    d.update(huffman_code_tree(r, binString + '1'))
    return d

def read_tree(node, binstr):

    bits_traversed = 0
    curr_node = node
    while(type(curr_node) == NodeTree) and len(binstr) != 0:
        if(binstr[0] == '0' and curr_node.has_left()):
            curr_node = curr_node.left
        elif(binstr[0] == '1' and curr_node.has_right()):
            curr_node = curr_node.right
        else:
            return curr_node, -1

        bits_traversed += 1
        binstr = binstr[1:]

    if(type(curr_node) == NodeTree):
        return None, -1

    return curr_node, bits_traversed


def regen_tree(node, value, binstr):

    curr_node = node

    while len(binstr) > 1:
        if(binstr[0] == '1'):
            if(curr_node.right == None):
                curr_node.right = NodeTree()
            curr_node = curr_node.right
        else:
            if(curr_node.left == None):
                curr_node.left = NodeTree()
            curr_node = curr_node.left
        binstr = binstr[1:]

    if(binstr[0] == '1'):
        curr_node.right = value
    else:
        curr_node.left = value

def make_tree(nodes):

    while len(nodes) > 1:
        (key1, c1) = nodes[-1]
        (key2, c2) = nodes[-2]
        nodes = nodes[:-2]
        node = NodeTree(key1, key2)
        nodes.append((node, c1 + c2))
        nodes = sorted(nodes, key=lambda x: x[1], reverse=True)
    return nodes[0][0]

def compress(data):

    num = np.array([[x, 0] for x in range(256)])
    for value in data:
        num[value][1] += 1

    freq = dict(num)
    freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    node = make_tree(freq)

    encoding = huffman_code_tree(node)
    encoding = sorted(encoding.items(), key=lambda x: (len(x[1]), x[0]), reverse=False)
    encoding = dict(encoding)

    bitstring = ""
    curr = '-1'
    for i in encoding:
        length = len(encoding[i])
        curr = format(int(curr, 2) + 1, f'0{len(curr)}b')
        if(len(curr) < length):
           curr += '0'*(length - len(curr))
        encoding.update({int(i): curr})

    for i in range(256):
        bitstring += format(len(encoding[i]), '08b')

    for i in data:
        bitstring += encoding[i]
    padding = (8 - len(bitstring) % 8) * '0'
    padding = 0 if padding == 8 else padding

    return format(len(padding), '08b') + bitstring + padding

def uncompress(data_in):

    encoding = np.array([[x, 0] for x in range(256)])
    data = data_in
    padding = data[0]
    data = data[1:]

    for i in range(256):
        byte = data[i]
        encoding[i][1] = byte
    data = data[256:]
    
    encoding = dict(sorted(encoding, key=lambda x: (x[1], x[0]), reverse=False))
    curr = '-1'
    huffman_tree = NodeTree()
    for i in encoding:
        length = encoding[i]
        curr = format(int(curr, 2) + 1, f'0{len(curr)}b')
        if(len(curr) < length):
           curr += '0'*(length - len(curr))
        encoding.update({int(i): curr})
        regen_tree(huffman_tree, i, encoding[i])

    binstr = ''
    output = []
    #NOTE:This section is extremely slow due to appending to a list
    #process is fast if writing straight into a file
    for i in range(len(data)):
        binstr += format(data[i], '08b')
        if(i == len(data)-1):
            binstr = binstr[:-padding]

        value, skip = read_tree(huffman_tree, binstr)
        while skip != -1:
            output.append(value)
            binstr = binstr[skip:]
            value, skip = read_tree(huffman_tree, binstr)

    return output
