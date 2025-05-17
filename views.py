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

# Funktion um einfaches Passwort zu erstellen
def einfachesPasswortErstellen(vergebenePasswörter, länge=6):
    while True:
        # String mit zufälliger Ziffer aus 0-9 der Länge k
        passwort = ''.join(random.choices('0123456789', k=länge))
        # prüft, ob das Passwort bereits vergeben wurde
        if passwort not in vergebenePasswörter:
            return passwort


# Funktion um Admin-Passwort zu erstellen
def adminPasswortErstellen(vergebenePasswörter, länge=10):
    while True:
        # String mit zufälliger Ziffer aus 0-9 der Länge k
        passwort = ''.join(random.choices('0123456789', k=länge))
        # prüft, ob das Passwort bereits vergeben wurde
        if passwort not in vergebenePasswörter:
            return passwort

# Gemeinden / Stadtverwaltungen aus CSV laden
def gemeindenLaden():
    gemeinden = []

    if os.path.isfile(gemeindenCSV):
        with open(gemeindenCSV, mode="r", encoding="utf-8-sig") as datei:
            reader = csv.DictReader(datei)
            for zeile in reader:
                typen = zeile.get("Typ")
                name = zeile.get("Gemeindename")
                gemeinden.append({'name': name, 'typ': typen})
    return gemeinden


# Funktion um E-Mails mit Passwörter zu versenden
def sendeMailMitCodes(request):
    erfolg = False # Variable, die später angibt, ob E-Mail erfolgreich versendet wurde
    emailAdresse = None # später E-Mail des Nutzers
    stadtverwaltungName = None # später Name der Stadtverwaltung / Gemeinde
    gemeinden = gemeindenLaden()

    if request.method == 'POST': # Formular mit POST-Methode gesendet
        emailAdresse = request.POST.get('email') # E-Mai-Adresse aus POST-Daten holen
        stadtverwaltungName = request.POST.get('stadtverwaltung') # Namen aus POST-Daten holen

        stadtverwaltungTyp = ""
        for gemeinde in gemeinden:
            if gemeinde["name"] == stadtverwaltungName:
                stadtverwaltungTyp = gemeinde["typ"]
                break

        if emailAdresse and stadtverwaltungName: # wenn E-Mail und Name vorhanden ist
            dateiExistiert = os.path.isfile(codeCSV) # prüft, ob die Datei bereits vorhanden ist

            # Vorhandene Passwörter und registrierte Stadtverwaltungen laden
            vergebenePasswörter = set()
            registrierteStadtverwaltungen = set()

            if dateiExistiert:
                with open(codeCSV, mode='r', encoding='utf-8') as datei:
                    # Datei als Dictionary lesen
                    reader = csv.DictReader(datei)
                    next(reader, None) # Kopfzeile überspringen
                    for zeile in reader:
                        # Wenn die Zeile gültig ist und alle benötigten Felder hat
                        if zeile.get("Stadtverwaltung") and zeile.get("Passwort") and zeile.get("Admin"):
                            # Stadtverwaltung und Passwörter hinzufügen
                            registrierteStadtverwaltungen.add(zeile["Stadtverwaltung"].strip())
                            vergebenePasswörter.add(zeile["Passwort"].strip())
                            vergebenePasswörter.add(zeile["Admin"].strip())

            # Prüfen, ob die Stadtverwaltung schon registriert wurde
            if stadtverwaltungName in registrierteStadtverwaltungen:
                return render(request, "KORA/Kontoerstellung.html", {
                    "success": False,
                    "email": emailAdresse,
                    "gemeinden": gemeinden,
                    "fehler": "Diese Stadt / Gemeinde wurde bereits registriert."
                })

            # Passwörter generieren
            einfaches_passwort = einfachesPasswortErstellen(vergebenePasswörter)
            # generierte Passwörter zu vergebene Passwörter hinzufügen 
            vergebenePasswörter.add(einfaches_passwort)
            admin_passwort = adminPasswortErstellen(vergebenePasswörter)
            vergebenePasswörter.add(admin_passwort)

            volleBezeichnung = f"{stadtverwaltungTyp} {stadtverwaltungName}"

            # Nachricht vorbereiten
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

            # E-Mail senden
            send_mail(
                'Ihre Zugangsdaten zum Projekt', # Betreff
                nachricht, # Textinhalt
                'buchung.kora@gmail.com', # Absendeadresse
                [emailAdresse], # Empfänger
                fail_silently=False, # bei Fehler Ausnahme werfen
            )

            # In CSV schreiben
            with open(codeCSV, mode='a', newline='', encoding='utf-8') as datei:
                writer = csv.writer(datei)
                if not dateiExistiert:
                    # Kopfzeile
                    writer.writerow(['Stadtverwaltung', 'Mail', 'Passwort', 'Admin'])
                # Daten schreiben
                writer.writerow([stadtverwaltungName, emailAdresse, einfaches_passwort, admin_passwort])

            erfolg = True

    return render(request, 'KORA/Kontoerstellung.html', {
        'success': erfolg,
        'email': emailAdresse,
        'gemeinden': gemeinden,
    })


# Funktion zur Anmeldung
def codeÜberprüfungAnmeldung(request):
    fehlermeldung = ""

    if request.method == "POST":
        eingegebenerCode = request.POST.get("code", "").strip()
        if not eingegebenerCode:
            fehlermeldung = "Bitte geben Sie einen Code ein."
        else:
            if os.path.isfile(codeCSV):
                with open(codeCSV, mode="r", encoding="utf-8") as datei:
                    reader = csv.DictReader(datei)
                    for zeile in reader:
                        einfach = zeile.get("Passwort", "").strip()
                        admin = zeile.get("Admin", "").strip()
                        stadtverwaltung = zeile.get("Stadtverwaltung", "").strip()
                        if eingegebenerCode == einfach:
                            request.session["stadtverwaltung"] = stadtverwaltung
                            request.session["rolle"] = "benutzer"
                            return redirect('Uebersicht')                            
                        elif eingegebenerCode == admin:
                            request.session["stadtverwaltung"] = stadtverwaltung
                            request.session["rolle"] = "admin"
                            return redirect("Adminverwaltung")                            
                        
            fehlermeldung = "Ungültiger Code. Bitte versuchen Sie es erneut."

    return render(request, "KORA/Einwahl.html", {
        "fehler": fehlermeldung
    })



def stockwerkeView(request):
    stadtverwaltung = request.session.get('stadtverwaltung')
    if not stadtverwaltung:
        return redirect("Einwahl.html")
    rolle = request.session['rolle']
    if rolle == "admin":
        return redirect("Adminverwaltung.html")
    
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
                    'Zustand': 'frei'
                })

    rfidDaten = {}
    with open(rfidCSV, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=',')
        for row in reader:
            if "Gemeindename" in row and row["Gemeindename"].strip() == stadtverwaltung.strip():
                rfidID = row['RFIDID']
                zustand = row['Zustand']
                chipID = row['ChipID']
                
                # Letzten Zustand für jede RFIDID speichern
                if rfidID not in rfidDaten:
                    rfidDaten[rfidID] = {
                        'Zustand': zustand,
                        'ChipID': chipID,
                        'Zeit': row['Zeit']  # Zeitstempel der Buchung
                    }
                else:
                    # Überprüfen, ob der aktuelle Zustand neuer ist
                    if rfidDaten[rfidID]['Zeit'] < row['Zeit']:
                        rfidDaten[rfidID]['Zustand'] = zustand
                        rfidDaten[rfidID]['ChipID'] = chipID
                        rfidDaten[rfidID]['Zeit'] = row['Zeit']
    for raum in raumdaten:
        rfidID = raum['RFIDID']
        
        if rfidID in rfidDaten:
            raum['ChipID'] = rfidDaten[rfidID]['ChipID']
            raum['Zustand'] = rfidDaten[rfidID]['Zustand']  # Letzten Zustand übernehmen


    sensorDaten = {}
    with open(temperaturCSV, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=',')
        for row in reader:
            if "Gemeindename" in row and row["Gemeindename"].strip() == stadtverwaltung.strip():
                sensorDaten[row['SensorID']] = {
                    'Temperatur': row['Temperatur'],
                    'Luftfeuchtigkeit': row['Luftfeuchtigkeit'],
                }

    for raum in raumdaten:
        sensorID = raum['SensorID']
        if sensorID in sensorDaten:
            raum['Temperatur'] = sensorDaten[sensorID]['Temperatur']
            raum['Luftfeuchtigkeit'] = sensorDaten[sensorID]['Luftfeuchtigkeit']

    # Räume nach Stockwerk gruppieren
    stockwerke_dict = defaultdict(list)
    for raum in raumdaten:
        stockwerke_dict[raum['Stockwerk']].append(raum)

    # Sortierte Stockwerke als Liste von Tupeln (Stockwerk, [Räume])
    sortierte_stockwerke = sorted(stockwerke_dict.items(), key=lambda x: x[0])  # sortiert numerisch/alphabetisch

    return render(request, 'KORA/Uebersicht.html', {
        'stockwerke': sortierte_stockwerke
    })




def auswahlView(request):
    stadtverwaltung = request.session.get('stadtverwaltung')
    if not stadtverwaltung:
        return redirect("Einwahl.html")
    rolle = request.session.get("rolle")
    if rolle == "admin":
        return redirect("Adminverwaltung.html")

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


def adminView(request):
    stadtverwaltung = request.session.get('stadtverwaltung')
    if not stadtverwaltung:
        return redirect("Einwahl.html")
    rolle = request.session.get("rolle")
    if rolle != "admin":
        return redirect("Uebersicht.html")
    return render(request, 'KORA/Adminverwaltung.html')

def persoanlView(request):
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

        # Datei lesen und aktualisieren
        neue_daten = []
        with open(mitarbeiterChipCSV, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['ChipID'] == chipid:
                    row['Mitarbeitername'] = neuer_name
                neue_daten.append(row)

        # Datei überschreiben
        with open(mitarbeiterChipCSV, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['Gemeindename', 'ChipID', 'Mitarbeitername']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(neue_daten)

        return redirect('Personalverwaltung.html') 

    # CSV anzeigen
    with open(mitarbeiterChipCSV, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            mitarbeiterliste.append({
                'Gemeindename': row['Gemeindename'],
                'ChipID': row['ChipID'],
                'Mitarbeitername': row['Mitarbeitername'] or ''
            })

    return render(request, 'KORA/Personalverwaltung.html', {
        'mitarbeiterliste': mitarbeiterliste
    })


def kontaktView(request):
    stadtverwaltung = request.session.get('stadtverwaltung')
    if not stadtverwaltung:
        return redirect("Einwahl.html")
    return render(request, 'KORA/Kontakt.html')

def Abmeldung(request):
    request.session.flush()

    session_file_path = os.path.join(settings.SESSION_FILE_PATH, f'sessionid{request.session.session_key}')
    if os.path.exists(session_file_path):
        os.remove(session_file_path)
    return redirect("Einwahl")



@csrf_exempt
def rfid_empfang(request):
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


def lade_raumdaten(pfad, stadtverwaltung):
    raumdaten = {}
    with open(pfad, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for zeile in reader:
            if zeile["Gemeindename"] == stadtverwaltung:
            # Schlüssel: RFIDID, Wert: Raumnummer
                raumdaten[zeile['RFIDID']] = zeile['Raumnummer']
    return raumdaten   

def vorhersage(request, rfid):
    stadtverwaltung = request.session.get('stadtverwaltung')
    if not stadtverwaltung:
        return redirect("Einwahl")
    rolle = request.session.get("rolle")
    if rolle == "admin":
        return redirect("Adminverwaltung")
    
    tag = request.GET.get('tag', 'Montag')

    daten = lese_rfid_daten(rfidCSV)  # Pfad anpassen

    if stadtverwaltung:
        daten = [eintrag for eintrag in daten if eintrag['Gemeindename'] == stadtverwaltung]

    belegung = berechne_belegung(rfid, tag, daten)
    uhrzeiten = [f"{i+6}:00" for i in range(14)]
    tage = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']

    raumdaten = lade_raumdaten(räumeCSV, stadtverwaltung)  # Pfad anpassen
    raumnummer = raumdaten.get(str(rfid), f"Raum {rfid}")  # Fallback: RFId selbst

    context = {
        'rfid': rfid,
        'raumnummer': raumnummer,
        'selected_day': tag,
        'belegung': belegung,
        'uhrzeiten': uhrzeiten,
        'tage': tage,
    }

    return render(request, 'KORA/Vorhersage.html', context)

def lese_rfid_daten(pfad=rfidCSV):
    daten = []
    with open(pfad, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for zeile in reader:
            # Zeit in datetime-Objekt umwandeln
            zeit = datetime.strptime(zeile['Zeit'], '%Y-%m-%d %H:%M:%S')
            daten.append({
                'Gemeindename': zeile['Gemeindename'],
                'RFIDID': zeile['RFIDID'],
                'Zustand': zeile['Zustand'],
                'Zeit': zeit,
                'ChipID': zeile['ChipID'],
            })
    return daten

def berechne_belegung(rfid, tag, daten):
    # tag z.B. "Montag", "Dienstag" ...
    # Stunden von 6 bis 19 Uhr => 14 Werte

    # Wochentag als Index (Montag=0)
    wochentag_index = ['Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag'].index(tag)

    belegung_stunden = [0]*14
    stunden_counter = defaultdict(int)

    # Filter nur Einträge mit dem gesuchten rfid und passendem Wochentag
    for eintrag in daten:
        if eintrag['RFIDID'] == rfid and eintrag['Zeit'].weekday() == wochentag_index:
            stunde = eintrag['Zeit'].hour
            if 6 <= stunde <= 19:
                idx = stunde - 6
                if eintrag['Zustand'] == 'kommen':
                    stunden_counter[idx] += 1
                elif eintrag['Zustand'] == 'gehen':
                    stunden_counter[idx] -= 1

    # kumulativ aufsummieren, um den aktuellen Belegungsstand pro Stunde zu bekommen
    summe = 0
    for i in range(14):
        summe += stunden_counter[i]
        belegung_stunden[i] = max(summe, 0)  # Nie negative Belegung

    return belegung_stunden
