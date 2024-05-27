"""Program to continuously query Eve's detector readings.
Useful for callibration and testing purposes. Program runs
indefinitely - use 'Ctrl + C' to stop program.

Author: JH
Date: Feb 2023

Sample command in windows CMD:
> python eve_detector_query.py --serial com11
"""

import serial
import time
import argparse # For running the script with options
import sys

# Select device com port
my_parser = argparse.ArgumentParser()
my_parser.add_argument('--serial', action='store', type=str, required=True, help='Sets the serial address of the Eve Arduino')
args = my_parser.parse_args()
ser = vars(args).get('serial')

baudrate = 38400
timeout = 0.1
dev = serial.Serial(ser,baudrate,timeout=timeout)

def main():
    # resolution = 5
    # number_of_points = 360 // (resolution)
    # angs = np.arange(0,359,resolution)
    # vols = np.zeros((len(angs), 2))
    # mc.MotorControl(str(self.deviceBox.currentText().split()[0]))
    try:
        while True:
        # for i in range(len(angs)):
            # motor.set_angle(angs[i])
		    # curr_angle = float(self.motor.get_angle())
		    # angleInput.setValue(self.curr_angle) #QDoubleSpinBox - See guiRcv.ui file
            # Query device
            dev.write('volts? '.encode())
            time.sleep(0.1)
            # Get reply - repeat
            reply = dev.readlines()
            vals = [val.decode().strip() for val in reply]
            print(vals)
            # vols[i, :] = [int(vals[0]), int(vals[1])]
    except KeyboardInterrupt:
        print('Program closed.')
        sys.exit()
    # print(max(vols[:,0]))
    # print(max(vols[:,1]))

if __name__=='__main__':
    main()