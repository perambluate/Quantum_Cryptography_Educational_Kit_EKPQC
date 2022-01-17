'''
Python wrapper program to receive a sequence of 16 bit keys (Bob)
without key sifting (it will be done manually).
Author: Qcumber 2018
'''

import serial
import sys
import time

# Function to convert to hex, with a predefined nbits
def tohex(val, nbits):
  return hex((val + (1 << nbits)) % (1 << nbits))

# Obtain device location
devloc_file = '../devloc_quantum.txt'
with open(devloc_file) as f:
    content = f.readlines()[0]
    if content[-1] == '\n':  # Remove an extra \n
        content = content[:-1]

# Obtain threshold
threshold_file = '../threshold.txt'
with open(threshold_file) as f:
    content = f.readlines()[0]
    if content[-1] == '\n':  # Remove an extra \n
        content = content[:-1]
threshold = float(content) # Get the float value

# Other parameters declarations
baudrate = 9600      # Default in Arduino
timeout = 0.1        # Serial timeout (in s).
serial_addr = "COM12" # Hard-coded for now

# Opens the receiver side serial port
receiver = serial.Serial(serial_addr, baudrate, timeout=timeout)

# Wait until the serial is ready
# Note: for some computer models, particularly MacOS, the program cannot
# talk to the serial directly after openin. Need to wait 1-2 second.
print("Opening the serial port...")
time.sleep(2)
print("Done\n")

# Starts the program
print("Bob, Are you ready? This is the key receiver program.")
print("Randomising basis bits using Arduino")

# Randomising the sequence
receiver.write('RNDBAS ')

# Block until receive reply
while True:
    if receiver.in_waiting:
        print(receiver.readlines()[0]) # Should display OK
        break

print("Arduino says he/she likes to choose the following bits:")

# Find out what is the key
receiver.write('SEQ? ')

# Block until receive 1st reply
while True:
    if receiver.in_waiting:
        bas_str = receiver.readlines()[0][:-1] # Remove the /n
        break

# Giving the reply in HEX format
bas_hex = tohex(int("0b"+bas_str, 0), 16) # Get int, and convert to 16 bit hex
print("Basis bits (in hex):", bas_hex[2:].zfill(4))

# Run the sequence
print("\nRunning the sequence and performing measurement...")
receiver.write('RXSEQ ')

# Block until receive reply
while True:
    if receiver.in_waiting:
        meas_str = receiver.readlines()[0][:-1] # Remove the /n
        break

# Obtain the measured bits
meas_arr = meas_str.split()
res_str = ''
for val in meas_arr:
    if int(val) > threshold: # Higher than threshold -> 0
        res_str += '0'
    else:               # Lower than threshold -> 1
        res_str += '1'

res_hex = tohex(int("0b"+res_str, 0), 16) # Get int, and convert to 16 bit hex
print("Measurement result bits (in hex):", res_hex[2:].zfill(4))
# print meas_arr # Debug
# print res_str # Debug

# Print last statement and exits the program
print("\nTask done. Please perform key sifting with Bob via public channel.")
