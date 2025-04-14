import random
import csv
import os
from django.core.mail import send_mail
from django.shortcuts import render
from django.conf import settings

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
    csvPfad = os.path.join(settings.BASE_DIR, '/var/www/django-projekt/KORA/Gemeinden.csv')
    gemeinden = []

    if os.path.isfile(csvPfad):
        with open(csvPfad, mode="r", encoding="utf-8-sig") as datei:
            reader = csv.DictReader(datei, delimiter=";")
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
            csv_path = os.path.join(settings.BASE_DIR, '/var/www/django-projekt/KORA/Code.csv') # Pfad zur Datei mit den vergebenen Codes
            dateiExistiert = os.path.isfile(csv_path) # prüft, ob die Datei bereits vorhanden ist

            # Vorhandene Passwörter und registrierte Stadtverwaltungen laden
            vergebenePasswörter = set()
            registrierteStadtverwaltungen = set()

            if dateiExistiert:
                with open(csv_path, mode='r', encoding='utf-8') as datei:
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
                return render(request, "KORA/signup.html", {
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
            with open(csv_path, mode='a', newline='', encoding='utf-8') as datei:
                writer = csv.writer(datei)
                if not dateiExistiert:
                    # Kopfzeile
                    writer.writerow(['Stadtverwaltung', 'Mail', 'Passwort', 'Admin'])
                # Daten schreiben
                writer.writerow([stadtverwaltungName, emailAdresse, einfaches_passwort, admin_passwort])

            erfolg = True

    return render(request, 'KORA/signup.html', {
        'success': erfolg,
        'email': emailAdresse,
        'gemeinden': gemeinden,
    })
