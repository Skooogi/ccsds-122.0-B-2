class SegmentHeader():

    #Holds all data about a segment
    #4.2

    def __init__(self):
        self.first_segment  = 0
        self.last_segment   = 0 
        self.num_segments   = 0 #8 bit (mod 256) uint
        self.bitDC          = 0 #5 bit (mod 32)  uint
        self.bitAC          = 0 #5 bit uint
        self.has_header_2   = 0 
        self.has_header_3   = 0 
        self.has_header_4   = 0 
        self.pad_width      = 0 #[0,7] uint
        
        self.header_2 = Header_2()
        self.header_3 = Header_3()
        self.header_4 = Header_4()

    def __str__(self):
        output  = str(self.first_segment)
        output += str(self.last_segment) 
        output += format(self.num_segments, '08b')
        output += format(self.bitDC, '05b')
        output += format(self.bitAC, '05b')
        output += '0' #reserved
        output += str(self.has_header_2)
        output += str(self.has_header_3)
        output += str(self.has_header_4)

        if(self.last_segment):
            output += format(self.pad_width, '03b')
            output += '00000' #reserved

        if(self.has_header_2):
            output += str(self.header_2)

        if(self.has_header_3):
            output += str(self.header_3)

        if(self.has_header_4):
            output += str(self.header_4)
        return output

class Header_2():

    def __init__(self):
        self.seg_byte_limit = 0 #27 bit uint
        self.dc_stop        = 0 
        self.bitplane_stop  = 0 #5 bit uint
        self.stage_stop     = 0 #2 bit uint
        self.use_fill       = 0

    def __str__(self):
        output  = format(self.seg_byte_limit, '027b')
        output += str(self.dc_stop)
        output += format(self.bitplane_stop, '05b')
        output += format(self.bitplane_stop, '02b')
        output += str(self.use_fill)
        output += '0000' #reserved
        return output


class Header_3():
    
    def __init__(self):
        self.segment_size   = 0 #20 bit uint
        self.opt_dc_select  = 0
        self.opt_ac_select  = 0

    def __str__(self):
        output  = format(self.segment_size, '020b')
        output += str(self.opt_dc_select)
        output += str(self.opt_ac_select)
        output += '00' #reserved
        return output

class Header_4():

    def __init__(self):
        self.dwt_type               = 1
        self.extended_pixel_depth   = 0 
        self.signed_pixels          = 0
        self.pixel_bitdepth         = 0 #4 bit uint
        self.image_width            = 0 #20 bit uint
        self.transpose_image        = 0
        self.code_word_length       = 0 #3 bit uint
        self.custom_weights         = 0
        self.custom_weight_HH_1     = 0 #2 bit uint
        self.custom_weight_HL_1     = 0 #2 bit uint
        self.custom_weight_LH_1     = 0 #2 bit uint
        self.custom_weight_HH_2     = 0 #2 bit uint
        self.custom_weight_HL_2     = 0 #2 bit uint
        self.custom_weight_LH_2     = 0 #2 bit uint
        self.custom_weight_HH_3     = 0 #2 bit uint
        self.custom_weight_HL_3     = 0 #2 bit uint
        self.custom_weight_LH_3     = 0 #2 bit uint
        self.custom_weight_LL_3     = 0 #2 bit uint

    def __str__(self):
        output  = str(self.dwt_type)
        output += '0'
        output += str(self.extended_pixel_depth)
        output += str(self.signed_pixels)
        output += format(self.pixel_bitdepth, '04b')
        output += format(self.image_width, '020b')
        output += str(self.transpose_image)
        output += format(self.code_word_length, '03b')
        output += str(self.custom_weights)
        output += format(self.custom_weight_HH_1, '02b')
        output += format(self.custom_weight_HL_1, '02b')
        output += format(self.custom_weight_LH_1, '02b')
        output += format(self.custom_weight_HH_2, '02b')
        output += format(self.custom_weight_HL_2, '02b')
        output += format(self.custom_weight_LH_2, '02b')
        output += format(self.custom_weight_HH_3, '02b')
        output += format(self.custom_weight_HL_3, '02b')
        output += format(self.custom_weight_LH_3, '02b')
        output += format(self.custom_weight_LL_3, '02b')
        output += '00000000000' #reserved
        return output
