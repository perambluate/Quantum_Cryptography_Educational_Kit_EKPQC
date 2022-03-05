'''
Python wrapper program to send 32 bits QKD keys via
quantum and classial channel
Author: Qcumber 2018
'''

import serial
import sys
import time
import numpy as np

# Parameter
rep_wait_time = 0.3  # Wait time between IR packets (in s).
wait_till_sync = 0.5   # Time to wait for Bob (until we are sure he is ready).

''' Helper functions '''

# Function to convert to hex, with a predefined nbits
def tohex(val, nbits):
    return hex((val + (1 << nbits)) % (1 << nbits))

def send4BytesC(message_str):
    if len(message_str) == 4:
        deviceC.write('SEND '.encode()) # Send identifier [BEL]x3 + A
        deviceC.write(b'\x07\x07\x07' + 'A'.encode()) # This is Alice (sender)
        time.sleep(rep_wait_time)
        deviceC.write('SEND '.encode()) # Send message
        deviceC.write(message_str.encode())
        print(message_str)
    else:
        print("The message is not 4 bytes. Please check again")

def recv4BytesC():
    deviceC.reset_input_buffer() # Flush all the garbages
    deviceC.write('RECV '.encode()) # Flag to recv (the header)
    state = 0   # 0: waiting for STX, 1: transmitting/ wait for ETX
    while True: # Block until receives a reply
        if deviceC.in_waiting:
            hex_string = deviceC.read(8).decode()
            print(f'hex_string: {hex_string}') #Debug
            print("state:", state)
            if hex_string == '7070742':  # 07-[BEL], 42-B (Header from Bob)
                # print ("Received message!") # Debug
                deviceC.write('RECV '.encode())   # Receive the message
                state = 1
            elif state == 1:
                break
    # Convert to ASCII string
    hex_list = list(map(''.join, list(zip(*[iter(hex_string)]*2))))
    ascii_string = "".join([chr(int("0x"+each_hex,0)) for each_hex in hex_list])
    print(ascii_string)
    time.sleep(rep_wait_time)  # Wait a bit so that "Eve" can listen more carefully :P
    return ascii_string

def sendKeyQ():
    print("Generating random polarisation sequence...")
    # Randomising polarisation choice and run the sequence
    deviceQ.write('RNDSEQ '.encode())
    # Block until receive reply
    while True:
        if deviceQ.in_waiting:
            print(deviceQ.readlines()[0].decode().strip()) # Should display OK
            break
    # Find out what is the key
    deviceQ.write('SEQ? '.encode())
    # Block until receive 1st reply
    while True:
        if deviceQ.in_waiting:
            reply_str = deviceQ.readlines()[0].decode().strip() # Remove the /n
            break
    # Obtain the binary string repr for val and bas bits
    val_str = ""
    bas_str = ""
    for bit in reply_str:
        val_str += str(int(bit) // 2)
        bas_str += str(int(bit) % 2)
    # Run the sequence
    print("Running the sequence...")
    deviceQ.write('TXSEQ '.encode())
    # Block until receive reply
    while True:
        if deviceQ.in_waiting:
            print(deviceQ.readlines()[0].decode().strip()) # Should display OK
            break
    # Return the value and basis binary strings
    print(val_str, bas_str)
    return val_str, bas_str

def keySiftAliceC(valA_str, basA_str):
    # Send ready confirmation to Alice
    send4BytesC("RDY!")
    print("Let's do it! Performing key sifting with Bob...")
    # Zeroth step: convert the bin string repr to 32 bit int
    valA_int = int("0b"+valA_str, 0)
    basA_int = int("0b"+basA_str, 0)
    # First step: Listens to Bob's basis
    basB_hex = recv4BytesC()   # in hex
    basB_int = int("0x"+basB_hex, 0)
    # Second step: Compare Alice and Bob's basis
    matchbs_int = ~ (basA_int ^ basB_int) # Perform matching operation
    # Third step: Send this matched basis back to Bob
    matchbs_hex = tohex(matchbs_int, 16) # Get the hex from int
    matchbs_int = int(matchbs_hex, 0) # Need to convert again from hex
    send4BytesC(matchbs_hex[2:].zfill(4)) # Sends this hex to Bob
    # Fourth step: Perform key sifting (in binary string)
    matchbs_str = np.binary_repr(matchbs_int, width=16)
    siftmask_str = ''
    for i in range(16): # 16 bits
        if matchbs_str[i] == '0' :
            siftmask_str += 'X'
        elif matchbs_str[i] == '1':
            siftmask_str += valA_str[i]
    # Remove all the X'es
    siftkey_str = ''
    for bit in siftmask_str:
        if bit == 'X':
            pass
        else:
            siftkey_str += bit
    # Return the final sifted key
    print(siftmask_str, siftkey_str)
    return siftkey_str

# Obtain device location
devloc_fileC = '../devloc_classical.txt'
devloc_fileQ = '../devloc_quantum.txt'
# with open(devloc_fileC) as f:
#     contentC = f.readlines()[0]
#     if contentC[-1] == '\n':  # Remove an extra \n
#         contentC = contentC[:-1]
# with open(devloc_fileQ) as f:
#     contentQ = f.readlines()[0]
#     if contentQ[-1] == '\n':  # Remove an extra \n
#         contentQ = contentQ[:-1]
serial_addrC = 'COM5' #contentC
serial_addrQ = 'COM3' #contentQ

# Other parameters declarations
baudrate = 38400      # Default in Arduino
timeout = 0.1        # Serial timeout (in s).

# Opens the sender side serial port
deviceC = serial.Serial(serial_addrC, baudrate, timeout=timeout)
deviceQ = serial.Serial(serial_addrQ, baudrate, timeout=timeout)

# Wait until the serial is ready
# Note: for some computer models, particularly MacOS, the program cannot
# talk to the serial directly after openin. Need to wait 1-2 second.
print("Opening the serial port...")
time.sleep(2)
print("Done\n")

# Secure key string (binary)
seckey_bin = ""
n_attempt = 1

# Start of the UI
print("Hi Alice, are you ready? Let's make the key!")

try:
    # Testing the public channel
    print("\nTesting the public channel...")

    print("You send --Test--")
    send4BytesC("Test")

    print("Bob replies", recv4BytesC())

    print("\nPublic channel seems okay... Sending the quantum keys...")

    # Performing key distribution
    while True:
        print("\nAttempt", n_attempt)
        time.sleep(wait_till_sync) # Wait until Bob is ready to receive key
        val_str, bas_str = sendKeyQ()
        #time.sleep(wait_till_sync) # Wait until Bob is ready to perform QKD
        key = keySiftAliceC(val_str, bas_str)
        seckey_bin = seckey_bin + key
        if len(seckey_bin) >= 32: # If the key is longer than 32 bits, stop operation
            break
        else:
            print("Done! You've got", len(key), "bits. Total length:", len(seckey_bin), "bits.")
            n_attempt +=1

    print("DONE. The task is completed.")

    # You've got the key!
    seckey_bin = seckey_bin[:32] # Trim to 32 bits
    seckey_hex = tohex(int("0b"+seckey_bin, 0), 32)
    # Some intrepreter introduces L at the end (which probably means long). Will remove them (cosmetic reason)
    if seckey_hex[-1] == "L":
        seckey_hex = seckey_hex[:-1]
    print("The 32 bit secret key is (in hex):", seckey_hex[2:].zfill(8))
    print("\n Congrats. Use the key wisely. Thank you!")

except KeyboardInterrupt:
    # End of program
    deviceC.write('#'.encode()) # Flag to force end listening
    print ("\nProgram interrupted. Thank you for using the program!")
    sys.exit()  # Exits the program
