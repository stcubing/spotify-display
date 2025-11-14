import serial
import time

ser = serial.Serial("COM6", 115200, timeout = 1)
time.sleep(2)

print("connected")


# ser.write(b"gurt\n")

# while True:
#     # reading any incoming serial messages
#     line = ser.readline().decode(errors="ignore").strip()
#     if line:
#         print("esp: " + line)
        

while True:
    
    message = input("enter (x/o): ")
    
    if message == "x":
        print("simulating full display refresh (led should be off)")
        ser.write(b"asdf\n")
    elif message == "o":
        print("simulating partial display refresh (led should be on)")
        ser.write(b"[time] asdf\n")
    else:
        print("invalid")
        
