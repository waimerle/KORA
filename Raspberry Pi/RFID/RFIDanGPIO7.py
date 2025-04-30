import RPi.GPIO as GPIO
import spidev
import time
from mfrc522 import MFRC522

# Setze GPIO-Modus
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Initialisiere SPI-Verbindung für MFRC522 an GPIO 7
spi = spidev.SpiDev()
spi.open(0, 1)  # SPI-Bus 0, Device 1 (CE1)
spi.max_speed_hz = 50000  # Setze die maximale Geschwindigkeit für SPI

# Initialisiere MFRC522 für GPIO 7
reader_gpio7 = MFRC522(bus=0, device=1, spd=50000, pin_mode=10, pin_rst=22)

# Variable zur Verfolgung der letzten UID
last_uid_gpio7 = None

try:
    print("Warte auf Karten an GPIO 7...")
    while True:
        # Anfordern einer Karte
        (status, tagType) = reader_gpio7.MFRC522_Request(reader_gpio7.PICC_REQIDL)
        if status == reader_gpio7.MI_OK:
            print("Karte erkannt an GPIO 7")
            (status, backData) = reader_gpio7.MFRC522_Anticoll()
            if status == reader_gpio7.MI_OK:
                uid = ''.join([str(i) for i in backData])
                if uid != last_uid_gpio7:  # Überprüfen, ob die UID sich geändert hat
                    print(f"GPIO 7 - Card UID: {uid}")
                    last_uid_gpio7 = uid  # UID speichern
                else:
                    print("Karte bereits erkannt, warte auf Entfernung...")
            time.sleep(0.5)  # Kurze Pause, um Mehrfacherkennung zu vermeiden
        else:
            last_uid_gpio7 = None  # Karte nicht mehr erkannt

        time.sleep(3)  # Kurze Pause zwischen den Anfragen

finally:
    GPIO.cleanup()
