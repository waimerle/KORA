from mfrc522 import MFRC522
import RPi.GPIO as GPIO
import time

reader = MFRC522()

try:
    print("Warte auf Karten...")
    while True:
        (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status == reader.MI_OK:
            (status, uid) = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                uid = ''.join([str(i) for i in uid])
                print(f"GPIO 8 - Card UID: {uid}")
                time.sleep(3)
except KeyboardInterrupt:
    print("Beendet durch Benutzer.")
finally:
    GPIO.cleanup()

