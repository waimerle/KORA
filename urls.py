from django.urls import path
from KORA import views as app_views
from . import views

urlpatterns = [
	path("signup.html", app_views.sendeMailMitCodes, name='signup'),

]
