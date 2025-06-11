from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Usuario,Estudiante,Profesor, Cargo,Intere, Horario, Inscripcion,FechaCargaNota, Actividad,Planificacion,Nota,AnioEscolar,Asistencia
from django.contrib.auth.forms import PasswordChangeForm
from datetime import time
import datetime
from django.utils import timezone
#------------------------------ Usuario ------------------------------#


class UploadFileForm(forms.Form):
    file = forms.FileField()
    
class FormularioLogin(AuthenticationForm):
	def __init__(self, *args, **kwargs):
		super(FormularioLogin, self).__init__(*args, **kwargs)
		self.fields['username'].widget.attrs['class'] = 'form-control'
		self.fields['username'].widget.attrs['placeholder'] = 'Nombre de Usuario'
		self.fields['password'].widget.attrs['class'] = 'form-control'
		self.fields['password'].widget.attrs['placeholder'] = 'Contraseña'

class FormularioUsuario(forms.ModelForm):
	usuario_administrador = forms.BooleanField(required=False)

	password1 = forms.CharField(label = 'Contraseña', widget = forms.PasswordInput(
		attrs = {
			'class': 'form-control',
			'placeholder': 'Ingrese su contraseña',
			'id': 'password1',
			'required': 'required',
			}
		)
	)


	password2 = forms.CharField(label = 'Contraseña de confirmación', widget = forms.PasswordInput(
		attrs = {
			'class': 'form-control',
			'placeholder': 'Ingrese nuevamente su contraseña',
			'id': 'password2',
			'required': 'required',
			}
		)
	)

	class Meta:
		model = Usuario
		fields = ('email', 'username', 'nombre', 'apellido', 'usuario_administrador')
		widgets = {
			'email': forms.EmailInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Correo electrónico',
				}
			),
			'nombre': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Nombre',

				}
			),
			'apellido': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Apellido',
				}
			),
			'username': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Cedula',
				}
			),
		}

	def clean_password2(self):
		password1 = self.cleaned_data.get('password1')
		password2 = self.cleaned_data.get('password2')
		if password1 != password2:
			raise forms.ValidationError('Contraseñas no coinciden')
		return password2

	def save(self, commit = True):
		usuario = super().save(commit = False)
		usuario.set_password(self.cleaned_data['password1'])
		if commit:
			usuario.save()
		return usuario



# Esta es para cambiarle la contraseña al usuario que esta logeado
class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = Usuario
        fields = ('old_password', 'new_password1', 'new_password2')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personaliza los widgets para aplicar clases de Bootstrap
        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña Antigua'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nueva Contraseña'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar Nueva Contraseña'})

class FormularioUsuarioEdicion(forms.ModelForm):
    
	class Meta:
		model = Usuario
		fields = ('email', 'username', 'nombre', 'apellido', 'usuario_administrador')
		widgets = {
			'email': forms.EmailInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Correo electrónico',
				}
			),
			'nombre': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Nombre',

				}
			),
			'apellido': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Apellido',
				}
			),
			'username': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Nombre de usuario',
				}
			),
		}

	def __init__(self, *args, **kwargs):
		super(FormularioUsuarioEdicion, self).__init__(*args, **kwargs)
		self.fields['usuario_administrador'].required = False

	def save(self, commit=True):
		usuario = super().save(commit=False)
		if commit:
			usuario.save()
		return usuario

# y esta es para cambiarle la contraseña en el modal
class FormularioCambioContraseña(PasswordChangeForm):

    class Meta:
        model = Usuario  # Asegúrate de que Usuario sea tu modelo de usuario
        fields = ('new_password1', 'new_password2')
        labels = {
            'new_password1': ('Nueva contraseña'),
            'new_password2': ('Confirmar nueva contraseña'),
        }

#------------------------------ Estudiante ------------------------------#

class EstudianteForm(forms.ModelForm):
	class Meta:
		model = Estudiante
		fields = ['tipo_cedula_estudiante', 'cedula_estudiante', 'nombre_estudiante', 'apellido_estudiante', 'telefono_estudiante','correo_estudiante','Sexo']
		label = {
			'tipo_cedula_estudiante': '',
			'cedula_estudiante': 'Cédula',
			'nombre_estudiante': 'Nombre',
			'apellido_estudiante': 'Apellido',
			'telefono_estudiante': 'Teléfono',
			'correo_estudiante':'EMAIL',
            'Sexo':'Sexo',
		}
		widgets = {
			'tipo_cedula_estudiante': forms.Select(
				choices=[('','Nacionalidad'), ('V-', 'V-'), ('E-', 'E-')],
				attrs = {
					'class': 'form-control'
				}
			),
			'cedula_estudiante': forms.TextInput(
				attrs={
					'class': 'form-control',
					'placeholder': 'Cédula'
				}
			),
			'nombre_estudiante': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Nombre'
				}
			),
			'apellido_estudiante': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Apellido'
				}
			),
			'telefono_estudiante': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Teléfono'
				}
			),
			'correo_estudiante': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'EMAIL'
				}
			),
            'Sexo': forms.Select(
				choices=[('','Indique su Sexo'), ('MASCULINO', 'MASCULINO'), ('FEMENINO', 'FEMENINO')],
				attrs = {
					'class': 'form-control'
				}
			),		
		}




#------------------------------ Cargo ------------------------------#


class CargoForm(forms.ModelForm):
	class Meta:
		model = Cargo
		fields = ['nombre_cargo']
		label = {
			'nombre_cargo': 'Especialidad',

		}
		widgets = {
			'nombre_cargo': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Especialidad'
				}
			),
   

		}
  
#------------------------------ Profesor ------------------------------#

class ProfesorForm(forms.ModelForm):
	class Meta:
		model = Profesor
		fields = ['tipo_cedula_profesor', 'cedula_profesor', 'nombre_profesor', 'apellido_profesor', 'telefono_Profesor','id_cargo']
		label = {
			'tipo_cedula_profesor': '',
			'cedula_profesor': 'Cedula',
			'nombre_profesor': 'Nombre',
			'apellido_profesor': 'Apellido',
			'telefono_Profesor': 'Telefono',
			'id_cargo': 'Especialidad',
			
		}
		widgets = {
			'tipo_cedula_profesor': forms.Select(
				choices=[('','Nacionalidad'), ('V-', 'V-'), ('E-', 'E-')],
				attrs = {
					'class': 'form-control'
				}
			),
			'cedula_profesor': forms.TextInput(
				attrs={
					'class': 'form-control',
					'placeholder': 'Cedula'
				}
			),
			'nombre_profesor': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Nombres Completo'
				}
			),
			'apellido_profesor': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Apellidos Completos'
				}
			),
			'telefono_Profesor': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Telefono Celular'
				}
			),
			'id_cargo': forms.Select(
				attrs = {
				'class':'form-control'
				}
			),
   	
		}
  

#------------------------------ GRUPO ------------------------------#

class IntereForm(forms.ModelForm):
	class Meta:
		model = Intere
		fields = [ 'nombre_grupo', 'descripcion_grupo','contador_estudiantes','status']
		label = {
			'nombre_grupo': 'Nombre',
			'descripcion_grupo': 'Apellido',
   			'contador_estudiantes':'Contador estudiante',
			'status': 'Estatus del Grupo',

		}
		widgets = {

			'nombre_grupo': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Nombre'
				}
			),
			'descripcion_grupo': forms.TextInput(
				attrs = {
					'class': 'form-control',
					'placeholder': 'Descripcion'
				}
			),
			'contador_estudiantes': forms.NumberInput(
				attrs = {
					'class':'form-control',
					'placeholder': 'contador_estudiantes'
				}
			),	
			'status': forms.Select(
				choices=[('DISPONIBLE', 'DISPONIBLE'), ('NO DISPONIBLE', 'NO DISPONIBLE')],
				attrs = {
					'class': 'form-control'
				}
			),   
   
 
		}
  
#------------------------------ Horario ------------------------------#
def generar_opciones_horas():
    opciones = []
    hora = datetime.time(8, 0)
    while hora <= datetime.time(16, 0):
        opciones.append((hora.strftime("%H:%M"), hora.strftime("%H:%M")))
        # avanzar media hora
        hora = (datetime.datetime.combine(datetime.date.today(), hora) + datetime.timedelta(minutes=30)).time()
    return opciones


class HorarioForm(forms.ModelForm):
    hora_inicio = forms.ChoiceField(choices=generar_opciones_horas())
    hora_final = forms.ChoiceField(choices=generar_opciones_horas())

    class Meta:
        model = Horario
        fields = ['semana_grupo', 'hora_inicio', 'hora_final', 'id_g', 'id_p', 'id_ano']
        widgets = {
            'id_g': forms.Select(attrs={'class': 'form-control'}),
            'semana_grupo': forms.Select(
                choices=[
                    ('', 'Selecciona un Día'),
                    ('Lunes', 'Lunes'),
                    ('Martes', 'Martes'),
                    ('Miercoles', 'Miércoles'),
                    ('Jueves', 'Jueves'),
                    ('Viernes', 'Viernes')
                ],
                attrs={'class': 'form-control'}
            ),
            'id_p': forms.Select(attrs={'class': 'form-control'}),
            'id_ano': forms.Select(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        anio_activo = AnioEscolar.objects.filter(activo=True).first()
        if anio_activo:
            # Mostrar todos los grupos disponibles sin importar si tienen horarios asignados
            self.fields['id_g'].queryset = Intere.objects.filter(status='DISPONIBLE')
        else:
            self.fields['id_g'].queryset = Intere.objects.none()
        self.fields['id_ano'].queryset = AnioEscolar.objects.filter(activo=True)




    def clean(self):
        cleaned_data = super().clean()
        hora_inicio_str = cleaned_data.get('hora_inicio')
        hora_final_str = cleaned_data.get('hora_final')
        id_p = cleaned_data.get('id_p')
        id_ano = cleaned_data.get('id_ano')

        # Convertir a objetos datetime.time
        try:
            hora_inicio = datetime.datetime.strptime(hora_inicio_str, '%H:%M').time()
            hora_final = datetime.datetime.strptime(hora_final_str, '%H:%M').time()
        except (TypeError, ValueError):
            raise ValidationError('El formato de hora es inválido.')

        # Validaciones de hora
        hora_min = datetime.time(8, 0)
        hora_max = datetime.time(16, 0)

        if hora_inicio < hora_min or hora_inicio > hora_max:
            self.add_error('hora_inicio', 'La hora de inicio debe ser entre las 08:00 AM y 04:00 PM.')

        if hora_final < hora_min or hora_final > hora_max:
            self.add_error('hora_final', 'La hora final debe ser entre las 08:00 AM y 04:00 PM.')

        if hora_inicio >= hora_final:
            raise ValidationError('La hora de inicio debe ser menor que la hora final.')

        # Validar que el profesor no tenga otro grupo de interés en el mismo año escolar
        if id_p and id_ano:
            conflicto = Horario.objects.filter(id_p=id_p, id_ano=id_ano)
            if self.instance.pk:
                conflicto = conflicto.exclude(pk=self.instance.pk)

            if conflicto.exists():
                raise ValidationError(
                    f'El profesor {id_p} ya tiene un grupo de interés asignado en el año escolar {id_ano}.'
                )
        # Validar que el profesor no tenga otro grupo de interés en el mismo año escolar

        return cleaned_data
#------------------------------ Inscripcion ------------------------------#
      
class InscripcionForm(forms.ModelForm):
    class Meta:
        model = Inscripcion
        fields = ['id_estudiante', 'id_g','seccion','ano_curso','id_ano']
        labels = {
            'id_estudiante': 'Estudiante',
            'id_g': 'Grupo',
            'ano_curso': 'Año Cursante',
            'seccion': 'Seccion',
            'id_ano': 'Año Escolar',
        }
        widgets = {
            'id_estudiante': forms.Select(attrs={'class': 'form-control'}),
            'id_g': forms.Select(attrs={'class': 'form-control'}),
            
             'ano_curso': forms.Select(
				choices=[('','Selecciona el año cursante'), ('1er', '1er'), ('2do', '2do'), ('3ero', '3ero'), ('4to', '4to'), ('5to', '5to')],
				attrs = {
					'class': 'form-control'
				}),           
            
            'seccion': forms.Select(
				choices=[('','Selecciona la Seccion'), ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'),('F', 'F'),('G', 'G')],
				attrs = {
					'class': 'form-control'
				}),
            
            'id_ano': forms.Select(
				attrs = {
				'class':'form-control'
				}
			),
            
		}    
    def __init__(self, *args, **kwargs):
        super(InscripcionForm, self).__init__(*args, **kwargs)
        # Filtrar grupos disponibles
        self.fields['id_g'].queryset = Intere.objects.filter(status='DISPONIBLE')  # Cambia 'disponible' por el estado que consideres
        self.fields['id_ano'].queryset = AnioEscolar.objects.filter(activo=True)


    
    def clean(self):
        cleaned_data = super().clean()
        estudiante = cleaned_data.get('id_estudiante')
        anio_escolar = cleaned_data.get('id_ano')
        grupo = cleaned_data.get('id_g')

        if grupo:
            profesor_asignado = Horario.objects.filter(id_g=grupo).exists()
            if not profesor_asignado:
                raise ValidationError('Este grupo aún no tiene un profesor asignado en el horario.')

        if estudiante and anio_escolar:
            conflicto = Inscripcion.objects.filter(
                id_estudiante=estudiante,
                id_ano=anio_escolar
            )
            if self.instance.pk:
                conflicto = conflicto.exclude(pk=self.instance.pk)

            if conflicto.exists():
                raise ValidationError(
                    f'El estudiante {estudiante} ya está inscrito en un grupo de interés en el año escolar {anio_escolar}.'
                )

        return cleaned_data
#------------------------------ Planificacion ------------------------------#


class PlanificacionForm(forms.ModelForm):
    class Meta:
        model = Planificacion
        fields = ['nombre_pla', 'fecha_inicio', 'fecha_final', 'observacion', 'limite_actividades']
        labels = {
            'nombre_pla': 'Nombre de la Planificación *',
            'fecha_inicio': 'Fecha de Inicio *',
            'fecha_final': 'Fecha Final *',
            'observacion': 'Observación',
            'limite_actividades': 'Límite de Actividades',
        }
        widgets = {
            'nombre_pla': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_final': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Observación'}),
            'limite_actividades': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        anio_activo = AnioEscolar.objects.filter(activo=True).first()
        if user and anio_activo:
            grupos_profesor = Horario.objects.filter(
                cedula_profesor=user.username,
                id_ano=anio_activo
            ).values_list('id_g', flat=True)
            # Si el campo id_g está en el formulario, limita queryset (opcional)
            if 'id_g' in self.fields:
                self.fields['id_g'].queryset = Intere.objects.filter(id_g__in=grupos_profesor)
        else:
            if 'id_g' in self.fields:
                self.fields['id_g'].queryset = Intere.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_final = cleaned_data.get('fecha_final')

        if fecha_inicio and fecha_final:
            if fecha_final < fecha_inicio:
                self.add_error('fecha_final', 'Verifique la Fechas de la Planificación.')
        return cleaned_data
    
class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['nombre_actividad', 'descripcion_actividad', 'fecha_Actividad','evaluada']
        labels = {
            'nombre_actividad': 'Nombre de la Actividad *',
            'descripcion_actividad': 'Descripción de la Actividad',
            'fecha_Actividad': 'Fecha de la Actividad',
            'evaluada': '¿La actividad fue evaluada?',
        }
        widgets = {
            'nombre_actividad': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion_actividad': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_Actividad': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'evaluada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Puedes agregar filtros si el formulario tuviera campos de FK visibles

    def clean(self):
        cleaned_data = super().clean()
        fecha_actividad = cleaned_data.get('fecha_Actividad')
        # `id_pla` viene asignado desde la vista, no del formulario
        planificacion = getattr(self.instance, 'id_pla', None)

        if planificacion and fecha_actividad:
            if not (planificacion.fecha_inicio <= fecha_actividad <= planificacion.fecha_final):
                raise ValidationError(
                    f"La fecha de la actividad debe estar entre {planificacion.fecha_inicio} y {planificacion.fecha_final}."
                )

            actividades_existentes = Actividad.objects.filter(id_pla=planificacion)
            if self.instance.pk:
                actividades_existentes = actividades_existentes.exclude(pk=self.instance.pk)

            if actividades_existentes.count() >= planificacion.limite_actividades:
                raise ValidationError(
                    f"Ya has alcanzado el límite de {planificacion.limite_actividades} actividades para esta planificación."
                )

        return cleaned_data
#------------------------------ Nota ------------------------------#

class NotaForm(forms.ModelForm):
    def __init__(self, *args, lapso_actual=None, **kwargs):
        self.lapso_actual = lapso_actual
        super().__init__(*args, **kwargs)

        campos_lapsos = ['corte_1', 'corte_2', 'corte_3']
        
        today = timezone.now().date()
        year = today.year

        rango_cortes = {
            'corte_1': (datetime.date(year, 12, 10), datetime.date(year, 12, 31)),
            'corte_2': (datetime.date(year, 4, 15), datetime.date(year, 4, 29)),
            'corte_3': (datetime.date(year, 6, 10), datetime.date(year, 6, 30)),
        }

        for campo in campos_lapsos:
            self.fields[campo].required = False
            self.fields[campo].widget.attrs['readonly'] = True
            self.fields[campo].widget.attrs['disabled'] = True

        if lapso_actual and lapso_actual in rango_cortes:
            inicio, fin = rango_cortes[lapso_actual]
            if inicio <= today <= fin:
                self.fields[lapso_actual].required = True
                self.fields[lapso_actual].widget.attrs.pop('readonly', None)
                self.fields[lapso_actual].widget.attrs.pop('disabled', None)


    class Meta:
        model = Nota
        fields = ['corte_1', 'corte_2', 'corte_3']
        widgets = {
            'corte_1': forms.NumberInput(attrs={'step': '0', 'min': '0', 'max': '20'}),
            'corte_2': forms.NumberInput(attrs={'step': '0', 'min': '0', 'max': '20'}),
            'corte_3': forms.NumberInput(attrs={'step': '0', 'min': '0', 'max': '20'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        today = timezone.now().date()
        year = today.year

        rango_cortes = {
            'corte_1': (datetime.date(year, 12, 10), datetime.date(year, 12, 31)),
            'corte_2': (datetime.date(year, 4, 15), datetime.date(year, 4, 29)),
            'corte_3': (datetime.date(year, 6, 10), datetime.date(year, 6, 30)),
        }

        if self.lapso_actual:
            valor = cleaned_data.get(self.lapso_actual)
            if valor is not None:
                inicio, fin = rango_cortes[self.lapso_actual]
                if not (inicio <= today <= fin):
                    self.add_error(
                        self.lapso_actual,
                        ValidationError(
                            f"❌ Las notas del {self.lapso_actual.replace('_', ' ')} solo se pueden registrar "
                            f"del {inicio.strftime('%d/%m')} al {fin.strftime('%d/%m')}."
                        )
                    )
        return cleaned_data
# año escola ------------------------------------



class AnioEscolarForm(forms.ModelForm):
    fecha_inicio = forms.DateField(
        label='Fecha de inicio',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    fecha_fin = forms.DateField(
        label='Fecha de fin',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    activo = forms.BooleanField(
        label='Año activo',
        required=False,
        help_text='Solo puede haber un año escolar activo a la vez.',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = AnioEscolar
        fields = ('fecha_inicio', 'fecha_fin', 'activo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Las clases de los widgets ya están configuradas arriba, no necesitas repetir aquí

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            if fecha_inicio >= fecha_fin:
                raise forms.ValidationError("La fecha de fin debe ser posterior a la fecha de inicio.")

            # Evitar solapamiento con otros años escolares
            conflicto = AnioEscolar.objects.filter(
                fecha_inicio__lt=fecha_fin,
                fecha_fin__gt=fecha_inicio
            )
            if self.instance.pk:
                conflicto = conflicto.exclude(pk=self.instance.pk)

            if conflicto.exists():
                raise forms.ValidationError("Ya existe un año escolar que se superpone con este rango.")

        # Validar año activo único
        if cleaned_data.get('activo'):
            ya_activo = AnioEscolar.objects.filter(activo=True)
            if self.instance.pk:
                ya_activo = ya_activo.exclude(pk=self.instance.pk)
            if ya_activo.exists():
                raise forms.ValidationError("Ya hay un año escolar activo. Desactiva el actual antes de activar otro.")

        return cleaned_data


# año escola ------------------------------------
# año escola ------------------------------------

class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ['id_estudiante', 'id_g', 'encuentro_numero', 'asistio', 'fecha_encuentro']
        widgets = {
            'fecha_encuentro': forms.DateInput(attrs={'type': 'date', 'max': timezone.now().date().isoformat()}),
        }

    def clean_fecha_encuentro(self):
        fecha = self.cleaned_data.get('fecha_encuentro')
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError("La fecha no puede ser mayor a la de hoy.")
        return fecha
    

# año escola ------------------------------------
# año escola ------------------------------------

class FechaCargaNotaForm(forms.ModelForm):
    class Meta:
        model = FechaCargaNota
        fields = [
            'corte_1_inicio', 'corte_1_fin',
            'corte_2_inicio', 'corte_2_fin',
            'corte_3_inicio', 'corte_3_fin',
        ]

    corte_1_inicio = forms.DateField(
        label='Primer Corte Inicio',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    corte_1_fin = forms.DateField(
        label='Primer Corte Fin',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    corte_2_inicio = forms.DateField(
        label='Segundo Corte Inicio',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    corte_2_fin = forms.DateField(
        label='Segundo Corte Fin',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    corte_3_inicio = forms.DateField(
        label='Tercer Corte Inicio',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    corte_3_fin = forms.DateField(
        label='Tercer Corte Fin',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )




    def clean(self):
        cleaned_data = super().clean()

        # Extraer fechas
        c1_ini = cleaned_data.get('corte_1_inicio')
        c1_fin = cleaned_data.get('corte_1_fin')
        c2_ini = cleaned_data.get('corte_2_inicio')
        c2_fin = cleaned_data.get('corte_2_fin')
        c3_ini = cleaned_data.get('corte_3_inicio')
        c3_fin = cleaned_data.get('corte_3_fin')

        # Verificar que ninguna fecha de fin sea menor que la de inicio
        cortes = [
            (c1_ini, c1_fin, 'Corte 1'),
            (c2_ini, c2_fin, 'Corte 2'),
            (c3_ini, c3_fin, 'Corte 3'),
        ]

        for inicio, fin, nombre in cortes:
            if inicio and fin and fin < inicio:
                self.add_error(None, f"La fecha de fin del {nombre} no puede ser anterior a la fecha de inicio.")

        # Verificar que no haya solapamiento entre cortes
        rangos = []
        for ini, fin in [(c1_ini, c1_fin), (c2_ini, c2_fin), (c3_ini, c3_fin)]:
            if ini and fin:
                rangos.append((ini, fin))

        for i in range(len(rangos)):
            for j in range(i+1, len(rangos)):
                r1_ini, r1_fin = rangos[i]
                r2_ini, r2_fin = rangos[j]
                # Si se solapan: hay intersección entre los rangos
                if r1_ini <= r2_fin and r2_ini <= r1_fin:
                    raise ValidationError("Las fechas de los cortes no pueden superponerse entre sí.")