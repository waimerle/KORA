from django.urls import path
from KORA import views as app_views
from . import views

urlpatterns = [
    path("Kontoerstellung.html", app_views.sendeMailMitCodes, name='Kontoerstellung'),
    path("Einwahl.html", app_views.codeÜberprüfungAnmeldung, name='Einwahl'),
    path("Uebersicht.html", app_views.stockwerkeView, name='Uebersicht'),
    path("Info.html", app_views.auswahlView, name='Info'),
    path("Adminverwaltung.html", app_views.adminView, name= 'Adminverwaltung'),
    path("Personalverwaltung.html", app_views.persoanlView, name= 'Personalverwaltung'),
    path("Kontakt.html", app_views.kontaktView, name='Kontakt'),
    path("abmelden", app_views.Abmeldung, name='abmelden'),
    path("rfid-empfang/", app_views.rfid_empfang, name="rfid_empfang"),
    
]
