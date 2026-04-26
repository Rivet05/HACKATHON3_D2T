from django.db import models

class Hospital(models.Model):
    name = models.CharField(max_length=200)
    lat = models.FloatField()
    lng = models.FloatField()
    urgences_disponibles = models.BooleanField(default=True)
    specialites = models.JSONField(default=list)
    temps_attente_min = models.IntegerField(default=0)
    node_id = models.CharField(max_length=100) 
    last_status_update = models.DateTimeField(auto_now=True) # Nouveau pour Twist 02

    def __str__(self):
        return self.name

class RouteAuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    depart_lat = models.FloatField()
    depart_lng = models.FloatField()
    depart_nom = models.CharField(max_length=200, null=True, blank=True)
    hopital_choisi = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True)
    hopitaux_consideres = models.JSONField()
    raison_choix = models.TextField()
    eta_minutes = models.FloatField()
    nb_noeuds_explores = models.IntegerField()
    temps_calcul_ms = models.IntegerField()
    path_geojson = models.JSONField()
    
    # Nouveaux champs Twist 02
    fraicheur_donnees = models.JSONField(default=dict)
    recalculs = models.JSONField(default=list)
    destination_changee = models.BooleanField(default=False)

    def __str__(self):
        return f"Audit {self.timestamp} - {self.hopital_choisi}"
