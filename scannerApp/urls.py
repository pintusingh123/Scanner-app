from django.urls import path
from scannerApp.views import home,generate_qr , scan_qr

urlpatterns=[
 path('', home, name='home'),
 path('generateqr/', generate_qr, name='generateqr'),
 path('scanqr/' ,scan_qr, name='scanqr')

]