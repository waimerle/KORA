import random
import csv
import os
import json
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.conf import settings

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
                })

    rfidDaten = {}
    with open(rfidCSV, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=',')
        for row in reader:
            if "Gemeindename" in row and row["Gemeindename"].strip() == stadtverwaltung.strip():
                rfidDaten[row['RFIDID']] = {
                    'Zustand': row['Zustand'],
                    'ChipID': row['ChipID'],
                }


    for raum in raumdaten:
        rfidID = raum['RFIDID']
        if rfidID in rfidDaten:
            raum['Zustand'] = rfidDaten[rfidID]['Zustand']
            raum['ChipID'] = rfidDaten[rfidID]['ChipID']

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




    return render(request, 'KORA/Uebersicht.html', {'raumdaten': raumdaten})



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
                })

    rfidDaten = {}
    with open(rfidCSV, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=',')
        for row in reader:
            if "Gemeindename" in row and row["Gemeindename"].strip() == stadtverwaltung.strip():
                rfidDaten[row['RFIDID']] = {
                    'Zustand': row['Zustand'],
                    'ChipID': row['ChipID'],
                }

    for raum in raumdaten:
        rfidID = raum['RFIDID']
        if rfidID in rfidDaten:
            raum['Zustand'] = rfidDaten[rfidID]['Zustand']
            raum['ChipID'] = rfidDaten[rfidID]['ChipID']

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

    chipDaten = {}
    with open(mitarbeiterChipCSV, mode='r', encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=',')
        for row in reader:
            if "Gemeindename" in row and row["Gemeindename"].strip() == stadtverwaltung.strip():
                chipDaten[row['ChipID']] = {
                    'Mitarbeitername': row['Mitarbeitername'],
                }

    for raum in raumdaten:
        chipID = raum.get('ChipID')
        if chipID in chipDaten:
            raum['Mitarbeitername'] = chipDaten[chipID]['Mitarbeitername']

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
    return render(request, 'KORA/Personalverwaltung.html')

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

