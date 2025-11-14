import serial
import time

ser = serial.Serial("COM6", 115200, timeout = 1)
time.sleep(2)

print("connected")


ser.write(b"gurt\n")

while True:
    ser.write(b"asjdfkl")
    line = ser.readline().decode(errors="ignore").strip()
    if line:
        print("esp: " + line)