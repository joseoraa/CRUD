from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Inscripcion, Intere

# Actualizar el contador al inscribir un estudiante
