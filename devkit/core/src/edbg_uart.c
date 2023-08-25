#include "atmel_start.h"
#include "atmel_start_pins.h"
#include "driver_init.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct File {

    uint32_t num_packets;
    size_t received_packets;
    size_t data_index;
    uint32_t data_length;
    uint8_t* data;
} File;

typedef struct Packet {
    uint8_t length;
    uint8_t data[64];
    uint8_t crc;
} Packet;

static File* file;
static Packet cached_packet;
static uint8_t success = 0;
static uint8_t fail = 1;

static char error_msg[19] = "UART ERROR!";
static uint8_t message_length = 0;
static uint8_t message_data[256];
static volatile uint32_t data_arrived = 0;
static volatile uint32_t data_sent = 0;
static bool receiving_file = 0;
static bool sending_file = 0;

static uint8_t const crc8_table[] = {
    0xea, 0xd4, 0x96, 0xa8, 0x12, 0x2c, 0x6e, 0x50, 0x7f, 0x41, 0x03, 0x3d,
    0x87, 0xb9, 0xfb, 0xc5, 0xa5, 0x9b, 0xd9, 0xe7, 0x5d, 0x63, 0x21, 0x1f,
    0x30, 0x0e, 0x4c, 0x72, 0xc8, 0xf6, 0xb4, 0x8a, 0x74, 0x4a, 0x08, 0x36,
    0x8c, 0xb2, 0xf0, 0xce, 0xe1, 0xdf, 0x9d, 0xa3, 0x19, 0x27, 0x65, 0x5b,
    0x3b, 0x05, 0x47, 0x79, 0xc3, 0xfd, 0xbf, 0x81, 0xae, 0x90, 0xd2, 0xec,
    0x56, 0x68, 0x2a, 0x14, 0xb3, 0x8d, 0xcf, 0xf1, 0x4b, 0x75, 0x37, 0x09,
    0x26, 0x18, 0x5a, 0x64, 0xde, 0xe0, 0xa2, 0x9c, 0xfc, 0xc2, 0x80, 0xbe,
    0x04, 0x3a, 0x78, 0x46, 0x69, 0x57, 0x15, 0x2b, 0x91, 0xaf, 0xed, 0xd3,
    0x2d, 0x13, 0x51, 0x6f, 0xd5, 0xeb, 0xa9, 0x97, 0xb8, 0x86, 0xc4, 0xfa,
    0x40, 0x7e, 0x3c, 0x02, 0x62, 0x5c, 0x1e, 0x20, 0x9a, 0xa4, 0xe6, 0xd8,
    0xf7, 0xc9, 0x8b, 0xb5, 0x0f, 0x31, 0x73, 0x4d, 0x58, 0x66, 0x24, 0x1a,
    0xa0, 0x9e, 0xdc, 0xe2, 0xcd, 0xf3, 0xb1, 0x8f, 0x35, 0x0b, 0x49, 0x77,
    0x17, 0x29, 0x6b, 0x55, 0xef, 0xd1, 0x93, 0xad, 0x82, 0xbc, 0xfe, 0xc0,
    0x7a, 0x44, 0x06, 0x38, 0xc6, 0xf8, 0xba, 0x84, 0x3e, 0x00, 0x42, 0x7c,
    0x53, 0x6d, 0x2f, 0x11, 0xab, 0x95, 0xd7, 0xe9, 0x89, 0xb7, 0xf5, 0xcb,
    0x71, 0x4f, 0x0d, 0x33, 0x1c, 0x22, 0x60, 0x5e, 0xe4, 0xda, 0x98, 0xa6,
    0x01, 0x3f, 0x7d, 0x43, 0xf9, 0xc7, 0x85, 0xbb, 0x94, 0xaa, 0xe8, 0xd6,
    0x6c, 0x52, 0x10, 0x2e, 0x4e, 0x70, 0x32, 0x0c, 0xb6, 0x88, 0xca, 0xf4,
    0xdb, 0xe5, 0xa7, 0x99, 0x23, 0x1d, 0x5f, 0x61, 0x9f, 0xa1, 0xe3, 0xdd,
    0x67, 0x59, 0x1b, 0x25, 0x0a, 0x34, 0x76, 0x48, 0xf2, 0xcc, 0x8e, 0xb0,
    0xd0, 0xee, 0xac, 0x92, 0x28, 0x16, 0x54, 0x6a, 0x45, 0x7b, 0x39, 0x07,
    0xbd, 0x83, 0xc1, 0xff
};

void _read(void) {}
void _write(void) {}
void _open(void) {}

static void tx_cb_EDBG_COM(const struct usart_async_descriptor *const io_descr) {
    data_sent = 1;
}

static void rx_cb_EDBG_COM(const struct usart_async_descriptor *const io_descr) {
	data_arrived = 1;
}

static void err_cb_EDBG_COM(const struct usart_async_descriptor *const io_descr) {
	io_write(&EDBG_COM.io, (uint8_t*)error_msg, 19);
}

static void print(const char* str) {

    while(data_sent == 0) {}
    data_sent = 0;
    io_write(&EDBG_COM.io, (uint8_t*)str, strlen(str));
}

static void write(uint8_t* data, uint8_t length) {

    while(data_sent == 0) {}
    data_sent = 0;
    io_write(&EDBG_COM.io, data, length);
}

static uint8_t crc8(uint8_t* data, uint8_t length) {
    uint8_t crc = 0;
    for(size_t i = 0; i < length; ++i) {
        crc = crc8_table[crc ^ data[i]];
    }
    return crc;
}

static void clear_buffer() {
    uint8_t temp;

    while(1) {
        if(data_arrived == 0) {
            continue;
        }

        while(io_read(&EDBG_COM.io, &temp, 1) == 1) {}
        data_arrived = 0;

        return;
    }
}

static uint8_t send_packet(Packet* packet) {
    
    uint8_t data[packet->length + 2];
    data[0] = packet->length+2;
    memcpy(&data[1], &packet->data, packet->length);
    data[packet->length + 1] = packet->crc;

    uint8_t ack = 255;
    for(uint8_t i = 0; i < 20; ++i) {
        io_write(&EDBG_COM.io, data, packet->length+2);
        clear_buffer();
        while(1) {
            if(data_arrived == 0) {
                continue;
            }

            while(io_read(&EDBG_COM.io, &ack, 1) == 1) {}
            data_arrived = 0;
            break;
        }

        if(ack == success) {
            return 0;
        }
        ack = 255;
    }
    return 1;
}

static void parse_packet(void) {


    if(receiving_file) {
        memcpy(&file->data[file->data_index], &message_data[1], message_length-2);
        file->received_packets++;
        file->data_index += message_length-2;

        if(file->received_packets == file->num_packets) {
            receiving_file = 0;
        }
        return;
    }

    uint8_t message_cache[256] = {};
    memcpy(&message_cache, &message_data[1], message_length-2);

    char* token = strtok((char*)&message_cache, " \0\n");
    while(token) {

        /*
        if(strcmp(token, "upload") == 0) {

            char msg[100] = {};

            file->received_packets = 0;
            file->num_packets = 0;
            if(file->data) {
                free(file->data);
                file->data = NULL;
            }

            file->data_length = *(uint32_t*)&message_cache[8];
            file->num_packets = *(uint32_t*)&message_cache[12];
            
            if(file->data_length <= 300000) {
                file->data = malloc(file->data_length);
            }

            if(file->data) {
                sprintf(msg, "Allocated file of size %lu B!", file->data_length);
                receiving_file = 1;
            }

            else {
                sprintf(msg, "Failed allocating file of size %lu B!", file->data_length);
            }

            print(msg);
        }

        else if(strcmp(token, "download") == 0) {
            print("sending");
            delay_ms(10);

            cached_packet.length = 8;
            *(uint32_t*)&cached_packet.data[0] = file->data_length;
            *(uint32_t*)&cached_packet.data[4] = file->num_packets;
            cached_packet.crc = crc8(&cached_packet.data[0], cached_packet.length);
            send_packet(&cached_packet);
        }
        */

        if(strcmp(token, "test") == 0) {
            cached_packet.length = 8;
            cached_packet.data[0] = 0;
            cached_packet.data[1] = 1;
            cached_packet.data[2] = 2;
            cached_packet.data[3] = 3;
            cached_packet.data[4] = 4;
            cached_packet.data[5] = 5;
            cached_packet.data[6] = 6;
            cached_packet.data[7] = 7;
            cached_packet.crc = crc8(&cached_packet.data[0], 8);
            send_packet(&cached_packet);
        }
        
        token = strtok(NULL, " ");
    }
}

int main(void)
{
	atmel_start_init();

	usart_async_register_callback(&EDBG_COM, USART_ASYNC_TXC_CB, tx_cb_EDBG_COM);
	usart_async_register_callback(&EDBG_COM, USART_ASYNC_RXC_CB, rx_cb_EDBG_COM);
    usart_async_register_callback(&EDBG_COM, USART_ASYNC_ERROR_CB, err_cb_EDBG_COM);
	usart_async_enable(&EDBG_COM);

    file = calloc(1, sizeof(File));
    data_sent = 1;


    size_t received = 0; 
	while (1) {
		if (data_arrived == 0) {
			continue;
		}

		while(io_read(&EDBG_COM.io, &message_data[received], 1) == 1) {
            received++;
		} 

        if(message_length == 0) {
            message_length = message_data[0];
        }

        if(received == message_length) {
            uint8_t crc = crc8(&message_data[1], message_length-2);
            crc ^= message_data[message_length-1];
            if(crc) {
                write(&fail,1);
            }
            else {
                write(&success,1);
            }
            parse_packet();
            received = 0;
            message_length = 0;
            memset(message_data, 0, sizeof(message_data));
        }
		data_arrived = 0;
	}
}
