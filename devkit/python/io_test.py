from threading import Thread
import crc8
import numpy as np
import os,sys
import serial
import serial.tools.list_ports
import time

def get_port():
    ports = list(serial.tools.list_ports.comports())
    ser = serial;
    for p in ports:
        if "EDBG" in p[1]:
            return serial.Serial(p[0])
    raise IOError("Board not plugged in!")


def print_banner():
    print(r"""
 ____     ____     ____    ____    ____       
/\  _`\  /\  _`\  /\  _`\ /\  _`\ /\  _`\     
\ \ \/\_\\ \ \/\_\\ \,\L\_\ \ \/\ \ \,\L\_\   
 \ \ \/_/_\ \ \/_/_\/_\__ \\ \ \ \ \/_\__ \   
  \ \ \L\ \\ \ \L\ \ /\ \L\ \ \ \_\ \/\ \L\ \ 
   \ \____/ \ \____/ \ `\____\ \____/\ `\____\
    \/___/   \/___/   \/_____/\/___/  \/_____/
               _      ___       ___           
             /' \   /'___`\   /'___`\         
            /\_, \ /\_\ /\ \ /\_\ /\ \        
            \/_/\ \\/_/// /__\/_/// /__       
               \ \ \  // /_\ \  // /_\ \      
                \ \_\/\______/ /\______/      
                 \/_/\/_____/  \/_____/       
                                              
                                              
          """)

def read_packet(ser):

    while True:
        byte_data = b''
        time.sleep(0.01)

        while ser.inWaiting() > 0:
            byte_data += ser.read(1)

        if(byte_data == b''):
            ser.write((1).to_bytes(1, 'big'))
            continue

        packet_length = byte_data[0]
        crc = byte_data[packet_length-1]
        check = crc8.calculate(byte_data[1:packet_length-1])
        if(check - crc):
            print("[I]>> requesting resend")
            ser.write((1).to_bytes(1, 'big'))

        else:
            ser.write((0).to_bytes(1, 'big'))
            print("[I]>> received 1/1")
            return byte_data

def send_packet(ser, data, packet, num_packets):

    crc = crc8.calculate(data)
    
    #Resend the packet max 10 times
    for i in range(10):
        #length + 2 = packet length + data + checksum
        ser.write((len(data)+2).to_bytes(1, 'big'))
        ser.write(data)
        ser.write((crc).to_bytes(1, 'big'))
        time.sleep(0.01)
        out = int.from_bytes(ser.read(1))
        if(out == 0):
            print(f'[O]>> received {packet + 1}/{num_packets}', end='\r')
            if(packet + 1 == num_packets):
                print()
            return 0;
        else:
            print(f'[I]>> resending {out}')

    return 1;

if __name__ == "__main__":
    ser = get_port()
    ser.baudrate = 115200
    ser.timeout = 1
    print_banner()
    print("Connected: yes, port: "+ ser.port + ", baud: " + str(ser.baudrate))

    while 1 :

        input_str = input("[I]>> ")
        if input_str == '':
            continue

        if input_str == 'exit' or input_str == 'q':
            ser.close()
            exit()

        elif input_str == 'clear':
            os.system('clear')
            print_banner()
            print("Connected: yes, port: "+ ser.port + ", baud: " + str(ser.baudrate))

        elif input_str == 'test':
            send_packet(ser, input_str.encode(), 0, 1);

            time.sleep(0.1)
            byte_data = read_packet(ser);
            print(byte_data)

        else: 
            send_packet(ser, input_str.encode(), 0, 1);
        """
        else:
            # send the character to the device
            data_bytes = 0
            if(input_str == ''):
                continue

            elif(input_str == 'upload'):

                input_str = input("[I]>> Input file:")
                file = open(input_str, "rb")
                data_bytes = file.read()
                
                file_data = "upload\0\0".encode()
                file_data += len(data_bytes).to_bytes(4, 'little')
                file_data += ((len(data_bytes)+63)//64).to_bytes(4, 'little')
                out = send_packet(ser, file_data, 0, 1)
                print("[O]>> "+out)
                if(out[0] == 'F'):
                    continue
            elif(input_str == 'download'):
                data_bytes = input_str.encode()

                input_str = input("[I]>> Output file:")
                file = open(input_str, "wb")

                out = send_packet(ser, data_bytes, 0, 1)
                print("[O]>> "+out)

                if(out == 'sending'):
                    byte_data = b''
                    time.sleep(0.05)
                    while ser.inWaiting() > 0:
                        byte_data += ser.read(1)

                    packet_length = byte_data[0]
                    crc = byte_data[packet_length-1]
                    check = crc8.calculate(byte_data[1:-1])

                    file_size = int.from_bytes(byte_data[1:5], byteorder='little')
                    num_packets = int.from_bytes(byte_data[5:9], byteorder='little')
                    print(f'[I]>> file size: {file_size} B, Packets: {num_packets}')
                    if(crc == check):
                        print("[I]>> received 1/1")
                        send_packet(ser,"success".encode(),0,1)
                    else:
                        print("[I]>> resending 1")
                        send_packet(ser,"resend".encode(),0,1)
                continue

            else:
                data_bytes = input_str.encode()
                
            num_packets = (len(data_bytes)+63)//64
            for block in range(0, len(data_bytes), 64):
                send_packet(ser, data_bytes[block:block+64], block//64, num_packets)
                """

