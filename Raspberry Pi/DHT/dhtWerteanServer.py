import time
import board
import adafruit_dht
import requests

# Sensor-Konfiguration
sensor1 = adafruit_dht.DHT11(board.D17, use_pulseio=False)
sensor2 = adafruit_dht.DHT11(board.D27, use_pulseio=False)

url = "http://[2001:7c0:2320:2:f816:3eff:fec1:da44]:8000/sensordaten/"

def read_sensor(sensor, sensor_id, gemeinde):
    for _ in range(3):  # Bis zu 3 Versuche
        try:
            temp = sensor.temperature
            humid = sensor.humidity
            if temp is not None and humid is not None:
                return temp, humid
        except RuntimeError:
            time.sleep(1)
    raise RuntimeError("Keine gültigen Sensordaten erhalten")

while True:
    for sensor, sid in [(sensor1, "1"), (sensor2, "2")]:
        try:
            temp, humid = read_sensor(sensor, sid, "Bad Urach")
            print(f"[{sid}] Temperatur: {temp} C, Feuchtigkeit: {humid}%")

            data = {
                "sensor_id": sid,
                "temperature": temp,
                "humidity": humid,
                "gemeindename": "Bad Urach"
            }
            response = requests.post(url, json=data)
            print(f"Serverantwort: {response.status_code}")

        except Exception as e:
            print(f"Fehler bei Sensor {sid}: {e}")

    time.sleep(5)  # 5 Sekunden Pause zwischen den Messungen
