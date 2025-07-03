import random
import csv
import os
import json
from collections import defaultdict
from datetime import datetime
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


codeCSV = '/var/www/django-projekt/KORA/Code.csv'
gemeindenCSV = '/var/www/django-projekt/KORA/Gemeinden.csv'
mitarbeiterChipCSV = '/var/www/django-projekt/KORA/MitarbeiterChip.csv'
räumeCSV = '/var/www/django-projekt/KORA/Raum.csv'
rfidCSV = '/var/www/django-projekt/KORA/RFID.csv'
temperaturCSV = '/var/www/django-projekt/KORA/Temperatur.csv'


def einfachesPasswortErstellen(vergebenePasswörter, länge=6): #generiert Passwort aus Ziffern mit 6 Stellen
    while True:
        passwort = ''.join(random.choices('0123456789', k=länge))
        if passwort not in vergebenePasswörter:
            return passwort


def adminPasswortErstellen(vergebenePasswörter, länge=10): #generiert Passwort aus Ziffern mit 10 Stellen
    while True:
        passwort = ''.join(random.choices('0123456789', k=länge))
        if passwort not in vergebenePasswörter:
            return passwort


def gemeindenLaden(): #liest Gemeinden.csv ein und extrahiert Namen und Typen der Gemeinden
    gemeinden = []
    if os.path.isfile(gemeindenCSV):
        with open(gemeindenCSV, mode="r", encoding="utf-8-sig") as datei:
            reader = csv.DictReader(datei)
            for zeile in reader:
                typ = zeile.get("Typ")
                name = zeile.get("Gemeindename")
                gemeinden.append({'name': name, 'typ': typ})
    return gemeinden


def sendeMailMitCodes(request): #Verarbeitung Anmeldeformular; Prüfung ob bereits registriert; E-Mail mit Zugangsdaten; Speichern der Daten in Code.csv
    erfolg = False 
    emailAdresse = None 
    stadtverwaltungName = None 
    gemeinden = gemeindenLaden()

    if request.method == 'POST': 
        emailAdresse = request.POST.get('email') 
        stadtverwaltungName = request.POST.get('stadtverwaltung') 

        stadtverwaltungTyp = ""
        for gemeinde in gemeinden:
            if gemeinde["name"] == stadtverwaltungName:
                stadtverwaltungTyp = gemeinde["typ"]
                break

        if emailAdresse and stadtverwaltungName: 
            dateiExistiert = os.path.isfile(codeCSV) 

            vergebenePasswörter = set()
            registrierteStadtverwaltungen = set()

            if dateiExistiert:
                with open(codeCSV, mode='r', encoding='utf-8-sig') as datei:
                    reader = csv.DictReader(datei)
                    for zeile in reader:
                        if zeile.get("Stadtverwaltung") and zeile.get("Passwort") and zeile.get("Admin"):
                            registrierteStadtverwaltungen.add(zeile["Stadtverwaltung"].strip())
                            vergebenePasswörter.add(zeile["Passwort"].strip())
                            vergebenePasswörter.add(zeile["Admin"].strip())

            if stadtverwaltungName in registrierteStadtverwaltungen:
                return render(request, "KORA/Kontoerstellung.html", {
                    "success": False,
                    "email": emailAdresse,
                    "gemeinden": gemeinden,
                    "fehler": "Diese Stadt / Gemeinde wurde bereits registriert."
                })

            einfaches_passwort = einfachesPasswortErstellen(vergebenePasswörter)
            vergebenePasswörter.add(einfaches_passwort)
            admin_passwort = adminPasswortErstellen(vergebenePasswörter)
            vergebenePasswörter.add(admin_passwort)

            volleBezeichnung = f"{stadtverwaltungTyp} {stadtverwaltungName}"

            nachricht = (
                f"Sehr geehrte Damen und Herren der {volleBezeichnung},\n\n"
                f"vielen Dank für Ihre Anmeldung.\n\n"
                f"Hier sind Ihre Zugangsdaten:\n"
                f"🔑 Einfaches Passwort: {einfaches_passwort}\n"
                f"🔐 Admin-Passwort: {admin_passwort}\n\n"
                f"Bitte bewahren Sie diese sicher auf.\n\n"
                f"Bei Fragen zur Hardwareausstattung oder bei Erweiterungswünschen wenden Sie sich bitte direkt an das KORA-Team.\n\n"
                f"Freundliche Grüße\n"
                f"Ihr Projektteam KORA"
            )

            send_mail(
                'Ihre Zugangsdaten zum Projekt',
                nachricht,
                'buchung.kora@gmail.com', 
                [emailAdresse],
                fail_silently=False, 
            )

            with open(codeCSV, mode='a', newline='', encoding='utf-8-sig') as datei:
                writer = csv.writer(datei)
                if not dateiExistiert:
                    writer.writerow(['Stadtverwaltung', 'Mail', 'Passwort', 'Admin'])
                writer.writerow([stadtverwaltungName, emailAdresse, einfaches_passwort, admin_passwort])

            erfolg = True

    return render(request, 'KORA/Kontoerstellung.html', {
        'success': erfolg,
        'email': emailAdresse,
        'gemeinden': gemeinden,
    })


def codeÜberprüfungAnmeldung(request): #Login per Code --> Prüfung, ob Zugangscode korrekt ist 
    fehlermeldung = ""

    if request.method == "POST":
        eingegebenerCode = request.POST.get("code", "").strip()
        if not eingegebenerCode:
            fehlermeldung = "Bitte geben Sie einen Code ein."
        else:
            if os.path.isfile(codeCSV):
                with open(codeCSV, mode="r", encoding="utf-8-sig") as datei:
                    reader = csv.DictReader(datei)
                    for zeile in reader:
                        einfachesPasswort = zeile.get("Passwort", "").strip()
                        adminPasswort = zeile.get("Admin", "").strip()
                        stadtverwaltung = zeile.get("Stadtverwaltung", "").strip()
                        if eingegebenerCode == einfachesPasswort:
                            request.session["stadtverwaltung"] = stadtverwaltung
                            request.session["rolle"] = "benutzer"
                            return redirect('Uebersicht')                            
                        elif eingegebenerCode == adminPasswort:
                            request.session["stadtverwaltung"] = stadtverwaltung
                            request.session["rolle"] = "admin"
                            return redirect("Raumverwaltung")                                    
            fehlermeldung = "Ungültiger Code. Bitte versuchen Sie es erneut."

    return render(request, "KORA/Einwahl.html", {
        "fehler": fehlermeldung
    })


def übersichtRäume(request): #zeigt Räume der Stadtverwaltung mit Raumdaten, Zustand und Sensorwerte; Gruppierung nach Stockwertke
    stadtverwaltung = request.session.get('stadtverwaltung')
    if not stadtverwaltung:
        return redirect("Einwahl")
    rolle = request.session['rolle']
    if rolle == "admin":
        return redirect("Raumverwaltung")
    
    raumdaten = []
    with open(räumeCSV, mode='r', encoding="utf-8-sig") as file:
         reader = csv.DictReader(file, delimiter=',')
         for zeile in reader:
             if "Gemeindename" in zeile and zeile["Gemeindename"].strip() == stadtverwaltung.strip():
                raumdaten.append({
                    'Gemeindename': zeile["Gemeindename"],
                    'Raumnummer': zeile["Raumnummer"],
                    'Stockwerk': zeile["Stockwerk"],
                    'SensorID': zeile["SensorID"],
                    'RFIDID': zeile["RFIDID"],
                    'Zustand': 'frei'
                })

    rfidDaten = {}
    with open(rfidCSV, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=',')
        for zeile in reader:
            if "Gemeindename" in zeile and zeile["Gemeindename"].strip() == stadtverwaltung.strip():
                rfidID = zeile['RFIDID']
                zustand = zeile['Zustand']
                chipID = zeile['ChipID']
                zeit = zeile['Zeit']

                if rfidID not in rfidDaten:
                    rfidDaten[rfidID] = {
                        'Zustand': zustand,
                        'ChipID': chipID,
                        'Zeit': zeit 
                    }
                else:
                    if rfidDaten[rfidID]['Zeit'] < zeit:
                        rfidDaten[rfidID]['Zustand'] = zustand
                        rfidDaten[rfidID]['ChipID'] = chipID
                        rfidDaten[rfidID]['Zeit'] = zeit

    for raum in raumdaten:
        rfidID = raum['RFIDID']
        if rfidID in rfidDaten:
            raum['ChipID'] = rfidDaten[rfidID]['ChipID']
            raum['Zustand'] = rfidDaten[rfidID]['Zustand'] 

    sensorDaten = {}
    with open(temperaturCSV, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=',')
        for zeile in reader:
            if "Gemeindename" in zeile and zeile["Gemeindename"].strip() == stadtverwaltung.strip():
                sensorDaten[zeile['SensorID']] = {
                    'Temperatur': zeile['Temperatur'],
                    'Luftfeuchtigkeit': zeile['Luftfeuchtigkeit'],
                }

    for raum in raumdaten:
        sensorID = raum['SensorID']
        if sensorID in sensorDaten:
            raum['Temperatur'] = sensorDaten[sensorID]['Temperatur']
            raum['Luftfeuchtigkeit'] = sensorDaten[sensorID]['Luftfeuchtigkeit']

    stockwerke_dict = defaultdict(list)
    for raum in raumdaten:
        stockwerke_dict[raum['Stockwerk']].append(raum)

    sortierte_stockwerke = sorted(stockwerke_dict.items(), key=lambda x: x[0])

    return render(request, 'KORA/Uebersicht.html', {
        'stockwerke': sortierte_stockwerke
    })


def infoRaumbelegung(request): #Infos zur Belegung; Raum- und Sensordatem; Verknü+pfung von Chip-ID mit Mitarbeitername
    stadtverwaltung = request.session.get('stadtverwaltung')
    if not stadtverwaltung:
        return redirect("Einwahl.html")
    rolle = request.session.get("rolle")
    if rolle == "admin":
        return redirect("Raumverwaltung.html")

    raumdaten = []
    with open(räumeCSV, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=',')
        for row in reader:
            if "Gemeindename" in row and row["Gemeindename"].strip() == stadtverwaltung.strip():
                raumdaten.append({
                    'Gemeindename': row["Gemeindename"],
                    'Raumnummer': row["Raumnummer"],
                    'Stockwerk': row["Stockwerk"],
                    'SensorID': row["SensorID"],
                    'RFIDID': row["RFIDID"],
                    'Zustand': 'frei',
                })

    # RFID-Daten mit Zeitstempel prüfen, um letzten Zustand zu erkennen
    rfidDaten = {}
    with open(rfidCSV, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=',')
        for row in reader:
            if row.get("Gemeindename", "").strip() == stadtverwaltung.strip():
                rfidID = row['RFIDID']
                zeit = row['Zeit']
                zustand = row['Zustand']
                chipID = row['ChipID']

                if rfidID not in rfidDaten or rfidDaten[rfidID]['Zeit'] < zeit:
                    rfidDaten[rfidID] = {
                        'Zustand': zustand,
                        'ChipID': chipID,
                        'Zeit': zeit
                    }

    # Zustand und ChipID zuweisen
    for raum in raumdaten:
        rfidID = raum['RFIDID']
        if rfidID in rfidDaten:
            letzterEintrag = rfidDaten[rfidID]
            zustand = letzterEintrag['Zustand']
            chipID = letzterEintrag['ChipID']

            if zustand == "kommen":
                raum['Zustand'] = "belegt"
                raum['ChipID'] = chipID
            else:  # gehen oder leer
                raum['Zustand'] = "frei"
                raum['ChipID'] = None

    # Temperatur- und Luftfeuchtigkeitsdaten ergänzen
    sensorDaten = {}
    with open(temperaturCSV, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=',')
        for row in reader:
            if row.get("Gemeindename", "").strip() == stadtverwaltung.strip():
                sensorDaten[row['SensorID']] = {
                    'Temperatur': row['Temperatur'],
                    'Luftfeuchtigkeit': row['Luftfeuchtigkeit'],
                }

    for raum in raumdaten:
        sensorID = raum['SensorID']
        if sensorID in sensorDaten:
            raum['Temperatur'] = sensorDaten[sensorID]['Temperatur']
            raum['Luftfeuchtigkeit'] = sensorDaten[sensorID]['Luftfeuchtigkeit']

    # Mitarbeiterdaten verknüpfen
    chipDaten = {}
    with open(mitarbeiterChipCSV, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=',')
        for row in reader:
            if row.get("Gemeindename", "").strip() == stadtverwaltung.strip():
                chipDaten[row['ChipID']] = {
                    'Mitarbeitername': row['Mitarbeitername'],
                }

    for raum in raumdaten:
        chipID = raum.get('ChipID')
        if chipID and chipID in chipDaten:
            raum['Mitarbeitername'] = chipDaten[chipID]['Mitarbeitername']
        else:
            raum['Mitarbeitername'] = None

    return render(request, 'KORA/Info.html', {'raumdaten': raumdaten})

def raumVerwaltungAdmin(request): #Raumdaten ändern oder neu anlegen
    stadtverwaltung = request.session.get('stadtverwaltung')
    if not stadtverwaltung:
        return redirect("Einwahl")

    rolle = request.session.get("rolle")
    if rolle != "admin":
        return redirect("Uebersicht.html")
        
# Wenn Formualar abgesendet werden die Daten ausgelesen 
    if request.method == 'POST':
        sensorid = request.POST.get('sensorid')
        neuer_stockwerk = request.POST.get('stockwerk')
        neue_raumnummer = request.POST.get('raumnummer')

        neue_daten = []
        with open(räumeCSV, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for zeile in reader:
                if (zeile.get('Gemeindename', '').strip() == stadtverwaltung.strip() and
                    zeile.get('SensorID') == sensorid):
                    # Raum aktualisieren
                    zeile['Stockwerk'] = neuer_stockwerk
                    zeile['Raumnummer'] = neue_raumnummer
                neue_daten.append(zeile)

        # Prüfen, ob der SensorID-Eintrag überhaupt vorhanden war, sonst wird neuer hinzufügen
        # any gibt TRUE zurück wenn eine Bedingung erfüllt ist 
        if not any(d.get('SensorID') == sensorid and d.get('Gemeindename', '').strip() == stadtverwaltung.strip() for d in neue_daten):
            neue_daten.append({
                'Gemeindename': stadtverwaltung,
                'Raumnummer': neue_raumnummer,
                'Stockwerk': neuer_stockwerk,
                'SensorID': sensorid,
                'RFIDID': sensorid,  # Annahme: RFIDID = SensorID
            })

        # Neue Raumdaten in CSV speichern 
        with open(räumeCSV, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['Gemeindename', 'Raumnummer', 'Stockwerk', 'SensorID', 'RFIDID']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(neue_daten)

        return redirect('Raumverwaltung')

    # --- GET-Request: Räume laden ---

    # Hardware-Anzahl aus Gemeinden.csv lesen falls fehhler wird auf null gesetzt 
    hardware_verfuegbar = 0
    with open(gemeindenCSV, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for zeile in reader:
            if zeile.get('Gemeindename', '').strip() == stadtverwaltung.strip():
                try:
                    hardware_verfuegbar = int(zeile.get('AnzahlHardware', 0))
                except ValueError:
                    hardware_verfuegbar = 0
                break

    # Räume aus CSV lesen und nach SensorID indizieren
    raeume_dict = {}
    with open(räumeCSV, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for zeile in reader:
            if zeile.get('Gemeindename', '').strip() == stadtverwaltung.strip():
                raeume_dict[zeile['SensorID']] = zeile

    # Liste mit allen Hardware IDs füllen, vorhandene Räume oder leere Einträge
    raeume_liste = []
    for i in range(1, hardware_verfuegbar + 1):
        sensorid_str = str(i)
        # wenn raum schon exisitiert hol alle daten zu diesem Sensor 
        if sensorid_str in raeume_dict:
            zeile = raeume_dict[sensorid_str]
            raeume_liste.append({
                'sensorid': zeile['SensorID'],
                'gemeindename': zeile['Gemeindename'],
                'raumnummer': zeile['Raumnummer'],
                'stockwerk': zeile['Stockwerk'],
                'rfidid': zeile['RFIDID'],
            })
        #wenn Raum noch nicht existiert dann füge leeren Raum hinzu 
        else:
            raeume_liste.append({
                'sensorid': sensorid_str,
                'gemeindename': stadtverwaltung,
                'raumnummer': '',
                'stockwerk': '',
                'rfidid': sensorid_str,
            })

    context = {
        'raeume': raeume_liste,
        'hardware_verfuegbar': hardware_verfuegbar,
        'hardware_range': range(hardware_verfuegbar),
    }

    return render(request, 'KORA/Raumverwaltung.html', context)

def persoanlVerwaltungAdmin(request): #Name der Mitarbeiter verknüpft mit Chip-ID
    stadtverwaltung = request.session.get('stadtverwaltung')
    if not stadtverwaltung:
        return redirect("Einwahl.html")
    rolle = request.session.get("rolle")
    if rolle != "admin":
        return redirect("Uebersicht.html")
    
    mitarbeiterliste = []

    # Falls Name aktualisiert wird
    if request.method == 'POST':
        chipid = request.POST.get('chipid')
        neuer_name = request.POST.get('mitarbeitername')

        neue_daten = []
        with open(mitarbeiterChipCSV, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for zeile in reader:
                if zeile.get('Gemeindename', '').strip() == stadtverwaltung.strip():
                    if zeile['ChipID'] == chipid:
                        zeile['Mitarbeitername'] = neuer_name
                neue_daten.append(zeile)

        with open(mitarbeiterChipCSV, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['Gemeindename', 'ChipID', 'Mitarbeitername']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(neue_daten)

        return redirect('Personalverwaltung.html') 

    # Nur Mitarbeiter der aktuellen Stadtverwaltung anzeigen
    with open(mitarbeiterChipCSV, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for zeile in reader:
            if zeile.get('Gemeindename', '').strip() == stadtverwaltung.strip():
                mitarbeiterliste.append({
                    'Gemeindename': zeile['Gemeindename'],
                    'ChipID': zeile['ChipID'],
                    'Mitarbeitername': zeile.get('Mitarbeitername', '') or ''
                })

    return render(request, 'KORA/Personalverwaltung.html', {
        'mitarbeiterliste': mitarbeiterliste
    })


def impressum(request):
    stadtverwaltung = request.session.get('stadtverwaltung')
    if not stadtverwaltung:
        return redirect("Einwahl")
    
    return render(request, 'KORA/Kontakt.html')


def abmeldung(request): #löschen der Session
    request.session.flush()

    return redirect("Einwahl")


@csrf_exempt
def rfidDatenEmpfang(request): #JSON-Daten mit RFID-Ereignisse annehmen --> RFID.csv 
    if request.method != "POST":
        return JsonResponse({"error": "Nur POST erlaubt"}, status=405)

    try:
        daten = json.loads(request.body)

        if "gemeinde" not in daten or "rfid_id" not in daten or "eintraege" not in daten:
            return JsonResponse({"error": "Fehlende Felder"}, status=400)

        aktueller_status = {}  # (gemeinde, rfid_id) -> chip_id oder None

        if os.path.exists(rfidCSV):
            with open(rfidCSV, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    key = (row["Gemeindename"], row["RFIDID"])
                    if row["Zustand"] == "kommen":
                        aktueller_status[key] = row["ChipID"]
                    elif row["Zustand"] == "gehen":
                        if key in aktueller_status and aktueller_status[key] == row["ChipID"]:
                            aktueller_status[key] = None

        with open(rfidCSV, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Gemeindename", "RFIDID", "Zustand", "Zeit", "ChipID"])

            if os.stat(rfidCSV).st_size == 0:
                writer.writeheader()

            for eintrag in daten["eintraege"]:
                gemeinde = daten["gemeinde"]
                rfid_id = str(daten["rfid_id"])
                chip_id = eintrag["rfid"]
                zeit = eintrag["zeit"]
                zustand = eintrag.get("status", "kommen")  # Status vom Pi übernehmen
                key = (gemeinde, rfid_id)

                aktuell_drin = aktueller_status.get(key)

                if zustand == "kommen":
                    if aktuell_drin is None:
                        aktueller_status[key] = chip_id
                    else:
                        return JsonResponse({"error": "Raum bereits belegt"}, status=403)

                elif zustand == "gehen":
                    if aktuell_drin == chip_id:
                        aktueller_status[key] = None
                    else:
                        return JsonResponse({"error": "Ungültiges Verlassen – andere Person ist drin"}, status=403)

                writer.writerow({
                    "Gemeindename": gemeinde,
                    "RFIDID": rfid_id,
                    "Zustand": zustand,
                    "Zeit": zeit,
                    "ChipID": chip_id
                })

        return JsonResponse({"status": "Daten gespeichert"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def lade_raumdaten(pfad, stadtverwaltung): #Hilfsfunktion --> holt Raumnummern der Stadtverwaltung aus CSV
    raumdaten = {}
    with open(pfad, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for zeile in reader:
            if zeile.get("Gemeindename", "").strip().lower() == stadtverwaltung.strip().lower():
                raumdaten[zeile['RFIDID']] = zeile['Raumnummer']
    return raumdaten   


def vorhersage(request, rfid): #Wie viele Leute waren pro Stunde dort?
    stadtverwaltung = request.session.get('stadtverwaltung')
    if not stadtverwaltung:
        return redirect("Einwahl")
    rolle = request.session.get("rolle")
    if rolle == "admin":
        return redirect("Raumverwaltung")
    
    tag = request.GET.get('tag', 'Montag')

    daten = leseRfidDaten(rfidCSV)

    if stadtverwaltung:
        datenGefiltert = []
        for eintrag in daten:
            if eintrag["Gemeindename"] == stadtverwaltung:
                datenGefiltert.append(eintrag)
        daten = datenGefiltert

    belegung = berechne_belegung(rfid, tag, daten)
    uhrzeiten = []
    for stunde in range(6, 20):
        uhrzeiten.append(f"{stunde}:00")
    tage = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']

    raumdaten = lade_raumdaten(räumeCSV, stadtverwaltung) 
    raumnummer = raumdaten.get(str(rfid), f"Raum {rfid}")

    context = {
        'rfid': rfid,
        'raumnummer': raumnummer,
        'selected_day': tag,
        'belegung': belegung,
        'uhrzeiten': uhrzeiten,
        'tage': tage,
    }

    return render(request, 'KORA/Vorhersage.html', context)


def leseRfidDaten(pfad = rfidCSV): #RFID.csv auslesen und Feld Zeit in echte Datumsobjekte konvertieren
    daten = []
    with open(pfad, newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for zeile in reader:
            try:
                zeit = datetime.strptime(zeile['Zeit'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                zeit = None

            daten.append({
                'Gemeindename': zeile.get('Gemeindename', ''),
                'RFIDID': zeile.get('RFIDID', ''),
                'Zustand': zeile.get('Zustand', ''),
                'Zeit': zeit,
                'ChipID': zeile.get('ChipID', ''),
            })

    return daten


def berechne_belegung(rfid, tag, daten): #Zählt jede Stunde (6-20), wie viele Personen im Raum sind. 

    wochentage = ['Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag']
    try:
        wochentagIndex = wochentage.index(tag)
    except ValueError:
        return [0]*14

    belegung_stunden = [0]*14
    stundenZähler = defaultdict(int)

    for eintrag in daten:
        if eintrag['RFIDID'] == rfid and eintrag['Zeit'].weekday() == wochentagIndex:
            stunde = eintrag['Zeit'].hour
            if 6 <= stunde <= 19:
                stundenIndex = stunde - 6
                if eintrag['Zustand'] == 'kommen':
                    stundenZähler[stundenIndex] += 1
                elif eintrag['Zustand'] == 'gehen':
                    stundenZähler[stundenIndex] -= 1

    summe = 0
    for stunde in range(14):
        summe += stundenZähler[stunde]
        belegung_stunden[stunde] = max(summe, 0)

    return belegung_stunden

@csrf_exempt
def dhtDatenEmpfang(request): #Sensordaten vom Pi --> Temperatur.csv
    
    if request.method != "POST":
        return JsonResponse({"error": "Nur POST erlaubt"}, status=405)
# geschickte Daten als json auslesen 
    try:
        daten = json.loads(request.body)

        
# wir merken uns, ob später ein Eintrag aktualisiert wurde 
        eintrag_aktualisiert = False
        neue_zeilen = []
# Spaltenüberschrift der CSV-Datei
        fieldnames = ["Gemeindename", "SensorID", "Temperatur", "Luftfeuchtigkeit"]
        
# geht jede Zeile durch, wenn Zeile denselben Sensor und Ort hat wie vom PI wird der Wert aktualisiert 
        if os.path.exists(temperaturCSV):
            with open(temperaturCSV, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["SensorID"] == str(daten["sensor_id"]) and row["Gemeindename"] == daten["gemeindename"]:
                        row["Temperatur"] = daten["temperature"]
                        row["Luftfeuchtigkeit"] = daten["humidity"]
                        eintrag_aktualisiert = True
                    neue_zeilen.append(row)
                    
# falls kein Eintrag vorhanden wird neuer hinzugefügt 
        if not eintrag_aktualisiert:
            neue_zeilen.append({
                "Gemeindename": daten["gemeindename"],
                "SensorID": str(daten["sensor_id"]),
                "Temperatur": daten["temperature"],
                "Luftfeuchtigkeit": daten["humidity"]
            })

# neue CSV Datei wird geschrieben 
        with open(temperaturCSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(neue_zeilen)

        return JsonResponse({"status": "Daten aktualisiert" if eintrag_aktualisiert else "Daten hinzugefügt"})

    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)
