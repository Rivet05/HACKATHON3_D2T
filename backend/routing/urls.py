from django.urls import path
from .views import RouteCalculationView, HospitalListUpdateView, HospitalDetailUpdateView, AuditLogListView
from . import views

urlpatterns = [
    path('route/', RouteCalculationView.as_view(), name='route-calculation'),
    path('hospitals/', HospitalListUpdateView.as_view(), name='hospital-list'),
    path('hospitals/<int:pk>/', HospitalDetailUpdateView.as_view(), name='hospital-update'),
    path('audit/', views.AuditLogListView.as_view(), name='audit-list'),
    path('traffic/inject_blockage/', views.InjectBlockageView.as_view(), name='inject-blockage'),
]
