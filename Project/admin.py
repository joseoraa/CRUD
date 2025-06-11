from django.contrib import admin
from .models import Usuario,Estudiante,Profesor,Cargo,Intere,Horario,Inscripcion,Planificacion,Actividad,Nota,Asistencia,AnioEscolar

# Register your models here.

admin.site.register(Usuario)
admin.site.register(Estudiante)
admin.site.register(Profesor)
admin.site.register(Cargo)
admin.site.register(Intere)
admin.site.register(Horario)
admin.site.register(Inscripcion)
admin.site.register(Planificacion)
admin.site.register(Actividad)
admin.site.register(Nota)
admin.site.register(Asistencia)
admin.site.register(AnioEscolar)