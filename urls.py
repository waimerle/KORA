from django.urls import path
from KORA import views as app_views
from . import views

urlpatterns = [
    path("Kontoerstellung.html", app_views.sendeMailMitCodes, name="Kontoerstellung"),
    path("Einwahl.html", app_views.codeÜberprüfungAnmeldung, name="Einwahl"),
    path("Uebersicht.html", app_views.übersichtRäume, name="Uebersicht"),
    path("Info.html", app_views.infoRaumbelegung, name="Info"),
    path("Raumverwaltung.html", app_views.raumVerwaltungAdmin, name= "Raumverwaltung"),
    path("Personalverwaltung.html", app_views.persoanlVerwaltungAdmin, name= "Personalverwaltung"),
    path("Kontakt.html", app_views.impressum, name="Kontakt"),
    path("abmelden", app_views.abmeldung, name="abmelden"),
    path("rfid-empfang/", app_views.rfidDatenEmpfang, name="rfid_empfang"),
    path("Vorhersage.html/<str:rfid>/", app_views.vorhersage, name="Vorhersage"),
    path("sensordaten/", app_views.dhtDatenEmpfang, name="dhtDatenEmpfang"),
    
]
