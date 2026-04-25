from rest_framework import serializers
from .models import Hospital, RouteAuditLog

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'

class RouteAuditLogSerializer(serializers.ModelSerializer):
    hopital_choisi_name = serializers.ReadOnlyField(source='hopital_choisi.name')
    
    class Meta:
        model = RouteAuditLog
        fields = '__all__'
