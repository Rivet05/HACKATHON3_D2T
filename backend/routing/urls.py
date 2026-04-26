from django.urls import path
from .views import RouteCalculationView, HospitalListUpdateView, HospitalDetailUpdateView, AuditLogListView
from . import views

urlpatterns = [
    path('route/', RouteCalculationView.as_view(), name='route-calculation'),
    path('hospitals/', HospitalListUpdateView.as_view(), name='hospital-list'),
    path('hospitals/<int:pk>/', HospitalDetailUpdateView.as_view(), name='hospital-update'),
    path('audit/', views.AuditLogListView.as_view(), name='audit-list'),
    path('route/integrity/', views.RouteIntegrityView.as_view(), name='route-integrity'),
    path('traffic/inject_blockage/', views.InjectBlockageView.as_view(), name='inject-blockage'),
    path('traffic/reset/', views.TrafficResetView.as_view(), name='traffic-reset'),
    path('hospitals/<int:pk>/sabotage/', views.SabotageHospitalView.as_view(), name='sabotage-hospital'),
]
