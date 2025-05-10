import requests
from mfrc522 import MFRC522
import RPi.GPIO as GPIO
import time
import datetime

reader = MFRC522()
url = "http://[2001:7c0:2320:2:f816:3eff:fec1:da44]:8000/rfid-empfang/"

def send_rfid_data(gemeinde, rfid_id, chip_id, zeit, status):
    data = {
        "gemeinde": gemeinde,
        "rfid_id": rfid_id,
        "eintraege": [
            {"zeit": zeit, "rfid": chip_id, "status": status}
        ]
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"Erfolgreich gesendet: {chip_id} um {zeit} mit Status: {status}")
        else:
            print(f"Fehler beim Senden der Daten {response.status_code}")
    except Exception as e:
        print("Fehler:", e)

try:
    print("Warte auf Karten...")
    uid_status = {}  # Dictionary zur Verfolgung des Status jeder UID

    while True:
        (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status == reader.MI_OK:
            (status, uid) = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                uid = ''.join([str(i) for i in uid])
                zeit = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                gemeinde = "Bad Urach"
                rfid_id = 1
                
                # Überprüfen, ob die UID bereits im Dictionary ist
                if uid not in uid_status:
                    uid_status[uid] = 0  # Initialisiere den Statuszähler für die UID

                # Bestimme den Status basierend auf dem Zähler
                uid_status[uid] += 1
                if uid_status[uid] % 2 == 1:
                    status_text = "kommen"  # Ungerade Anzahl: kommen
                else:
                    status_text = "gehen"   # Gerade Anzahl: gehen
                
                send_rfid_data(gemeinde, rfid_id, uid, zeit, status_text)
                time.sleep(3)
except KeyboardInterrupt:
    print("Beendet durch Benutzer.")
finally:
    GPIO.cleanup()
