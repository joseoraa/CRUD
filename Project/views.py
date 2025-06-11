import json
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.db import IntegrityError
from django.db.models import Count, Max
from django.forms.widgets import HiddenInput
from django.urls import reverse_lazy
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.generic import View, TemplateView, ListView, UpdateView, CreateView, DeleteView
from django.views.generic.edit import FormView
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, HttpResponseForbidden
from django import forms
from django.utils import timezone
from django.template.loader import get_template
from django.forms.utils import ErrorDict
from django.core.management import call_command
from django.conf import settings
from django.contrib import messages
from functools import wraps
from io import BytesIO
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.urls import reverse
from datetime import datetime, date, time
from collections import defaultdict
from django.forms import modelformset_factory
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.timezone import now

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image, PageBreak
)

from reportlab.lib.enums import TA_CENTER,TA_LEFT,TA_JUSTIFY,TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, mm

from .forms import (
    FormularioLogin, CustomPasswordChangeForm, FormularioUsuario, FormularioUsuarioEdicion,
    CargoForm, EstudianteForm, ProfesorForm, IntereForm, HorarioForm, InscripcionForm,
    PlanificacionForm, ActividadForm, NotaForm,AnioEscolarForm,FechaCargaNotaForm  
)
from .models import (
    Usuario, Estudiante, Profesor, Cargo, Intere, Horario, Inscripcion,
    Planificacion, Actividad, Nota, Asistencia,AnioEscolar,FechaCargaNota
)


#------------------------------ INICIO ------------------------------#

@login_required
def redireccion_inicio(request):
    if request.user.groups.filter(name='Administrador').exists():
        return redirect('home')  # admin
    elif request.user.groups.filter(name='Profesor').exists():
        return redirect('home_profesor')  # profesor
    else:
        return redirect('login')  # Por si no pertenece a ningún grupo
    
class Home(TemplateView):
    template_name = 'Inicio/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_staff:
            # Administrador: ver todo
            context['total_estudiantes'] = Estudiante.objects.count()
            context['total_profesores'] = Profesor.objects.count()
            context['total_grupos'] = Intere.objects.count()
            context['total_inscripcion'] = Inscripcion.objects.count()

        else:
            # Profesor normal: filtrar por su propia cédula
            cedula_profesor = user.username
            grupo_asignado = Horario.objects.filter(cedula_profesor=cedula_profesor).first()

            if grupo_asignado:
                planificaciones = Planificacion.objects.filter(id_g=grupo_asignado.id_g)
                actividades = Actividad.objects.filter(id_pla__in=planificaciones.values_list('id_pla', flat=True))
                estudiantes_inscritos = Inscripcion.objects.filter(id_g=grupo_asignado.id_g)

                context['total_planificaciones'] = planificaciones.count()
                context['total_actividades'] = actividades.count()
                context['total_estudiantes'] = estudiantes_inscritos.count()
                context['total_grupos'] = 1  # Solo su grupo
            else:
                context['total_planificaciones'] = 0
                context['total_actividades'] = 0
                context['total_estudiantes'] = 0
                context['total_grupos'] = 0

            context['total_profesores'] = 1  # Siempre el mismo profesor

        return context

#------------------------------ LOGIN y LOGAUT ------------------------------#
def login_view(request):
       # Lógica de autenticación aquí
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
           # Suponiendo que has autenticado al usuario
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, '¡Bienvenido al sistema!')
            return redirect('home')  # Redirige a la página principal

class Login(FormView):
    template_name = 'Inicio/login.html'
    form_class = AuthenticationForm
    success_url = reverse_lazy('home')

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        return super(Login, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()

        if user.cuenta_bloqueada:
            messages.error(self.request, 'Cuenta bloqueada. Por favor, contacte al administrador.')
            return self.form_invalid(form)
        
        login(self.request, user)
        # Reiniciar los intentos fallidos al iniciar sesión exitosamente
        user.intentos_fallidos = 0
        user.save()
        messages.success(self.request, f'Bienvenido al sistema, {user.nombre}!')
        return super(Login, self).form_valid(form)

    def form_invalid(self, form):
        username = form.cleaned_data.get('username')

        try:
            user = Usuario.objects.get(username=username)
            user.intentos_fallidos += 1

            if user.intentos_fallidos >= 3:
                user.cuenta_bloqueada = True
                messages.error(self.request, 'Cuenta bloqueada. Por favor, contacte al administrador.')
            else:
                attempts_left = 3 - user.intentos_fallidos
                messages.error(self.request, f'Contraseña incorrecta. Intentos fallidos: {user.intentos_fallidos}. Te quedan {attempts_left} intentos.')

            user.save()

        except Usuario.DoesNotExist:
            messages.error(self.request, 'Usuario no encontrado. Por favor, verifique el nombre de usuario.')

        return super(Login, self).form_invalid(form)
    


def logoutUsuario(request):
    logout(request)
    return HttpResponseRedirect('/accounts/login/')

@csrf_exempt  # Asegúrate de manejar CSRF adecuadamente en producción
def unlock_user(request, user_id):
    if request.method == 'POST':
        print(f"Request to unlock user: {user_id}")  # Para depuración
        try:
            user = Usuario.objects.get(pk=user_id)
            if user.cuenta_bloqueada:
                user.cuenta_bloqueada = False
                user.intentos_fallidos = 0
                user.save()
                return JsonResponse({'message': 'Usuario desbloqueado exitosamente.'})
            else:
                return JsonResponse({'message': 'El usuario ya está habilitado.'}, status=400)
        except Usuario.DoesNotExist:
            return JsonResponse({'message': 'Usuario no encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)  # Captura otros errores
    else:
        return JsonResponse({'message': 'Método no permitido.'}, status=405)
    
    
#------------------------------ Prueba ------------------------------#




#------------------------------ USUARIO ------------------------------#

class ListarUsuario(View):
    model = Usuario

    def get_queryset(self):
        return self.model.objects.all()
    
    

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(serialize('json', self.get_queryset()), 'application/json')
        else:
            return redirect('inicio_Usuario')

class RegistrarUsuario(CreateView):
    model = Usuario
    form_class = FormularioUsuario
    template_name = 'Usuario/registrarUsuario.html'

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST)
            if form.is_valid():
                nuevo_usuario = Usuario(
                    email = form.cleaned_data.get('email'),
                    username = form.cleaned_data.get('username'),
                    nombre = form.cleaned_data.get('nombre'),
                    apellido = form.cleaned_data.get('apellido')
                )
                nuevo_usuario.set_password(form.cleaned_data.get('password1'))
                nuevo_usuario.save()
                mensaje = f'El Usuario se ha registrado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'El Usuario no se ha podido registrar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Usuario')

class EditarUsuario(UpdateView):
    model = Usuario
    form_class = FormularioUsuarioEdicion
    template_name = 'Usuario/editarUsuario.html'
    context_object_name = 'usuario'

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, instance = self.get_object())
            if form.is_valid():
                form.save()
                mensaje = f'El Usuario se ha actualizado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'El Usuario no se ha podido actualizar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Usuario')

class EliminarUsuario(DeleteView):
    model = Usuario
    template_name = 'Usuario/eliminarUsuario.html'
    success_url = reverse_lazy('inicio_Usuario')
    context_object_name = 'usuario'

    def delete(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            usuario = self.get_object()
            usuario.delete()
            mensaje = f'El Usuario se ha eliminado correctamente'
            error = 'No hay error'
            response = JsonResponse({'mensaje': mensaje, 'error': error})
            response.status_code = 201
            return response
        else:
            return redirect('inicio_Usuario')
            
class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'registration/cambiocontraseña.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        # Llama al método de la clase base para cambiar la contraseña
        super().form_valid(form)
        # Agrega un mensaje de éxito
        messages.success(self.request, "Tu contraseña ha sido cambiada con éxito.")
        return super().form_valid(form)

class CambiarContraseñaModal(UpdateView):
    model = Usuario
    form_class = FormularioUsuario
    template_name = 'Usuario/cambiarContraseña.html'
    context_object_name = 'usuario'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['email'].widget = forms.HiddenInput()
        form.fields['username'].widget = forms.HiddenInput()
        form.fields['nombre'].widget = forms.HiddenInput()
        form.fields['apellido'].widget = forms.HiddenInput()
        form.fields['usuario_administrador'].widget = forms.HiddenInput()
        return form

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES, instance=self.get_object())
            if form.is_valid():
                form.save()
                mensaje = f'La Contraseña se ha actualizado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'La Contraseña no se ha podido actualizar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Usuario')
        
#------------------------------ Estudiantes ------------------------------#

class ListarEstudiante(View):
    model = Estudiante

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(serialize('json', self.get_queryset()), 'application/json')
        else:
            return redirect('inicio_Estudiante')

class EditarEstudiante(UpdateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = 'Estudiante/editarEstudiante.html'
    context_object_name = 'estudiante'

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES ,instance = self.get_object())
            if form.is_valid():
                form.save()
                mensaje = f'El Estudiante se ha actualizado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'El Estudiante no se ha podido actualizar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Estudiante')

class RegistrarEstudiante(CreateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = 'Estudiante/registrarEstudiante.html'

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                mensaje = f'El Estudiante se ha registrado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'El Estudiante no se ha podido registrar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Estudiante')

class EliminarEstudiante(DeleteView):
    model = Estudiante
    template_name = 'Estudiante/eliminarEstudiante.html'
    success_url = reverse_lazy('inicio_Estudiante')
    context_object_name = 'estudiante'

    def delete(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            estudiante = self.get_object()
            estudiante.delete()
            mensaje = f'El Estudiante se ha eliminado correctamente'
            error = 'No hay error'
            response = JsonResponse({'mensaje': mensaje, 'error': error})
            response.status_code = 201
            return response
        else:
            return redirect('inicio_Estudiante')

class BuscarEstudiantes(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        estudiantes = Estudiante.objects.filter(nombre_estudiante__icontains=query)
        results = [{'id': estudiante.id_estudiante, 'text': f'{estudiante.tipo_cedula_estudiante}{estudiante.cedula_estudiante} - {estudiante.nombre_estudiante} {estudiante.apellido_estudiante}'} for estudiante in estudiantes]
        return JsonResponse(results, safe=False)

#------------------------------ Cargo ------------------------------#

class ListarCargo(View):
    model = Cargo

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(serialize('json', self.get_queryset()), 'application/json')
        else:
            return redirect('inicio_Cargo')

class EditarCargo(UpdateView):
    model = Cargo
    form_class = CargoForm
    template_name = 'Cargo/editarCargo.html'
    context_object_name = 'cargo'

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES ,instance = self.get_object())
            if form.is_valid():
                form.save()
                mensaje = f'El Cargo se ha actualizado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'El Cargo no se ha podido actualizar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Cargo')

class RegistrarCargo(CreateView):
    model = Cargo
    form_class = CargoForm
    template_name = 'Cargo/registrarCargo.html'

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                mensaje = f'El Cargo se ha registrado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'El Cargo no se ha podido registrar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Cargo')

class EliminarCargo(DeleteView):
    model = Cargo
    template_name = 'Cargo/eliminarCargo.html'
    success_url = reverse_lazy('inicio_Cargo')
    context_object_name = 'cargo'

    def delete(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            cargo = self.get_object()
            cargo.delete()
            mensaje = f'El Cargo se ha eliminado correctamente'
            error = 'No hay error'
            response = JsonResponse({'mensaje': mensaje, 'error': error})
            response.status_code = 201
            return response
        else:
            return redirect('inicio_Cargo')

class BuscarCargos(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        cargos = Cargo.objects.filter(nombre_cargo__icontains=query)
        results = [{'id': cargo.id_cargo, 'text': cargo.nombre_cargo} for cargo in cargos]
        return JsonResponse(results, safe=False)

#------------------------------ Estudiantes ------------------------------#

class ListarProfesor(View):
    model = Profesor

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(serialize('json', self.get_queryset()), 'application/json')
        else:
            return redirect('inicio_Profesor')

class EditarProfesor(UpdateView):
    model = Profesor
    form_class = ProfesorForm
    template_name = 'Profesor/editarProfesor.html'
    context_object_name = 'profesor'
    
    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            profesor = self.get_object()
            context['profesor_data'] = {
                'tipo_cedula_profesor': profesor.tipo_cedula_profesor,
                'cedula_profesor': profesor.cedula_profesor,
                'nombre_profesor': profesor.nombre_profesor,
                'apellido_profesor': profesor.apellido_profesor,
                'telefono_Profesor': profesor.telefono_Profesor,
                'id_cargo': profesor.id_cargo.id_cargo,
                
            }
            return context
    
    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES ,instance = self.get_object())
            if form.is_valid():
                form.save()
                mensaje = f'El Profesor se ha actualizado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'El Profesor no se ha podido actualizar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Profesor')

class RegistrarProfesor(CreateView):
    model = Profesor
    form_class = ProfesorForm
    template_name = 'Profesor/registrarProfesor.html'

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                mensaje = f'El Profesor se ha registrado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'El Profesor no se ha podido registrar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Profesor')

class EliminarProfesor(DeleteView):
    model = Profesor
    template_name = 'Profesor/eliminarProfesor.html'
    success_url = reverse_lazy('inicio_Profesor')
    context_object_name = 'profesor'

    def delete(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            profesor = self.get_object()
            profesor.delete()
            mensaje = f'El Profesor se ha eliminado correctamente'
            error = 'No hay error'
            response = JsonResponse({'mensaje': mensaje, 'error': error})
            response.status_code = 201
            return response
        else:
            return redirect('inicio_Profesor')

class BuscarProfesores(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        profesores = Profesor.objects.filter(nombre_profesor__icontains=query)
        results = [{'id': profesor.id_p, 'text': f'{profesor.tipo_cedula_profesor}{profesor.cedula_profesor} - {profesor.nombre_profesor} {profesor.apellido_profesor}'} for profesor in profesores]
        return JsonResponse(results, safe=False)
     
#------------------------------ Grupo ------------------------------#
class ListarIntere(View):
    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            interes = Intere.objects.all()
            data = []
            for intere in interes:
                num_estudiante = Inscripcion.objects.filter(id_g=intere.id_g).count()  # Ensure correct filtering
                intere.contador_estudiantes = num_estudiante  # Update the contador_estudiantes
                data.append({
                    'id_g': intere.id_g,
                    'nombre_grupo': intere.nombre_grupo,
                    'descripcion_grupo': intere.descripcion_grupo,
                    'status': intere.status,
                    'contador_estudiantes': intere.contador_estudiantes,  # Use the updated value
                })
            return JsonResponse(data, safe=False)
        else:
            return redirect('inicio_Intere')

class EditarIntere(UpdateView):
    model = Intere
    form_class = IntereForm
    template_name = 'Intere/editarIntere.html'
    context_object_name = 'intere'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['contador_estudiantes'].widget = forms.HiddenInput()
        return form

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES ,instance = self.get_object())
            if form.is_valid():
                form.save()
                mensaje = f'El Grupo de Interes se ha actualizado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'El Grupo de Interes no se ha podido actualizar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Intere')

class RegistrarIntere(CreateView):
    model = Intere
    form_class = IntereForm
    template_name = 'Intere/registrarIntere.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['contador_estudiantes'].widget = forms.HiddenInput()
        return form

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                mensaje = f'El Grupo de Interes se ha registrado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'El Grupo de Interes no se ha podido registrar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Intere')

class EliminarIntere(DeleteView):
    model = Intere
    template_name = 'Intere/eliminarIntere.html'
    success_url = reverse_lazy('inicio_Intere')
    context_object_name = 'intere'

    def delete(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            intere = self.get_object()
            intere.delete()
            mensaje = f'El Grupo de Interes se ha eliminado correctamente'
            error = 'No hay error'
            response = JsonResponse({'mensaje': mensaje, 'error': error})
            response.status_code = 201
            return response
        else:
            return redirect('inicio_Intere')

class BuscarInteres(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        interes = Intere.objects.filter(nombre_grupo__icontains=query)
        results = [{'id': Intere.id_g, 'text': f'{intere.nombre_grupo}'} for intere in interes]
        return JsonResponse(results, safe=False)

#------------------------------ Grupo  con contador ------------------------------#  
class ListarHorario(View):
    model = Horario

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(serialize('json', self.get_queryset()), 'application/json')
        else:
            return redirect('inicio_Horario')

class EditarHorario(UpdateView):
    model = Horario
    form_class = HorarioForm
    template_name = 'Horario/editarHorario.html'
    context_object_name = 'horario'
        
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()  # obtener el horario
        form = self.form_class(instance=self.object)  # pasarle el horario existente
        context = self.get_context_data(form=form)
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = self.get_object()  # <-- cargar el horario que estás editando
            form = self.form_class(request.POST, request.FILES, instance=self.object)  # <-- importante!

            if form.is_valid():
                form.save()
                mensaje = 'El Horario se ha actualizado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 200  # <-- 200 (OK) mejor que 201 (CREATED) para edición
                return response
            else:
                mensaje = 'El Horario no se ha podido actualizar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
            
            
class RegistrarHorario(CreateView):
    model = Horario
    form_class = HorarioForm
    template_name = 'Horario/registrarHorario.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Filtrar grupos disponibles
        context['grupos_disponibles'] = Intere.objects.filter(status='DISPONIBLE')  # Cambia 'disponible' por el estado que consideres
        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                mensaje = 'El Horario se ha registrado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = 'El Horario no se ha podido registrar'
                # Aquí se obtienen los errores del formulario y del modelo
                error = {field: errors for field, errors in form.errors.items()}
                # Si hay errores de validación en el modelo, se añaden a la respuesta
                if hasattr(form, 'non_field_errors'):
                    non_field_errors = form.non_field_errors()
                    if non_field_errors:
                        error['non_field_errors'] = non_field_errors

                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response

class EliminarHorario(DeleteView):
    model = Horario
    template_name = 'Horario/eliminarHorario.html'
    success_url = reverse_lazy('inicio_Horario')
    context_object_name = 'horario'

    def delete(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            horario = self.get_object()
            horario.delete()
            mensaje = f'El Horario se ha eliminado correctamente'
            error = 'No hay error'
            response = JsonResponse({'mensaje': mensaje, 'error': error})
            response.status_code = 201
            return response
        else:
            return redirect('inicio_Horario')

class BuscarHorarios(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        horarios = Horario.objects.filter(semana_grupo__icontains=query)
        results = [{'id': horario.id_h, 'text': f'{horario.semana_grupo} {horario.hora_inicio} {horario.hora_final}'} for horario in horarios]
        return JsonResponse(results, safe=False)



#------------------------------ Listado ordenados por horario de gurpo coordinador ------------------------------#

def horarios_por_turno(request):
    # Obtener el año escolar activo
    anio_activo = AnioEscolar.objects.filter(activo=True).first()

    if not anio_activo:
        return render(request, 'Estudiante/horarios_por_turno.html', {
            'error': 'No hay un año escolar activo configurado.',
        })

    # Filtrar horarios por turno y año escolar activo
    horarios_manana = Horario.objects.filter(
        hora_inicio__gte=time(8, 0),
        hora_inicio__lt=time(12, 0),
        id_ano=anio_activo
    )

    horarios_tarde = Horario.objects.filter(
        hora_inicio__gte=time(12, 30),
        hora_inicio__lte=time(16, 0),
        id_ano=anio_activo
    )

    # Obtener estudiantes por grupo
    estudiantes_por_grupo = {}
    for horario in list(horarios_manana) + list(horarios_tarde):
        estudiantes = Inscripcion.objects.filter(id_g=horario.id_g)
        estudiantes_por_grupo[horario.id_g.id_g] = estudiantes

    context = {
        'horarios_manana': horarios_manana,
        'horarios_tarde': horarios_tarde,
        'estudiantes_por_grupo': estudiantes_por_grupo,
        'anio_activo': anio_activo.nombreano
    }

    return render(request, 'Estudiante/horarios_por_turno.html', context)

#------------------------------ Listado ordenados de gurpo coordinador ------------------------------#
@login_required
def listar_grupos_ordenados(request):
    grupo_filtro = request.GET.get('grupo')

    # Obtener año escolar activo
    anio_activo = AnioEscolar.objects.filter(activo=True).first()
    if not anio_activo:
        return render(request, 'Intere/listado_grupos.html', {
            'error': 'No hay un año escolar activo configurado.',
        })

    # Obtener actividades y filtrar si se especifica un grupo
    actividades = Actividad.objects.select_related('id_pla', 'id_g')
    if grupo_filtro:
        actividades = actividades.filter(id_g__id=grupo_filtro)

    actividades = actividades.order_by('nombre_grupo', 'nombre_pla', 'nombre_actividad')

    grupos_dict = {}
    profesores_dict = {}

    for act in actividades:
        grupo = act.nombre_grupo
        planificacion = act.nombre_pla

        # Filtrar por horario del año escolar activo
        horario = Horario.objects.filter(id_g=act.id_g, id_ano=anio_activo).first()
        if horario:
            profesor_nombre = f"{horario.nombre_profesor} {horario.apellido_profesor}"
            profesores_dict[grupo] = profesor_nombre
        else:
            continue  # Si no tiene horario activo, no lo mostramos

        grupos_dict.setdefault(grupo, {}).setdefault(planificacion, []).append(act)

    grupos = Intere.objects.all()

    return render(request, 'Intere/listado_grupos.html', {
        'grupos_dict': grupos_dict,
        'profesores_dict': profesores_dict,
        'grupos': grupos,
        'grupo_filtro': grupo_filtro,
        'anio_activo': anio_activo.nombreano
    })

#------------------------------ PRUEBA ------------------------------#
@never_cache
@login_required
def ver_grupo_por_cedula(request):
    cedula_profesor = request.user.username
    anio_activo = AnioEscolar.objects.filter(activo=True).first()

    if not anio_activo:
        messages.error(request, '❌ No hay un año escolar activo configurado.')
        return render(request, 'Planificacion/consultargrupo.html')

    grupo_asignado = Horario.objects.filter(
        cedula_profesor=cedula_profesor,
        id_ano=anio_activo
    ).first()

    planificaciones = []
    actividades = []
    planificacion = None
    limite = 0
    mostrar_form_actividades = False

    planificacion_form = PlanificacionForm(user=request.user)
    actividad_forms = None

    # ------------------------------------------
    # Paso 1: Registrar planificación
    # ------------------------------------------
    if request.method == 'POST' and 'nombre_pla' in request.POST:
        planificacion_form = PlanificacionForm(request.POST, user=request.user)
        if planificacion_form.is_valid():
            if grupo_asignado:
                planificacion = planificacion_form.save(commit=False)
                planificacion.id_g = grupo_asignado.id_g
                planificacion.save()

                request.session['planificacion_id'] = planificacion.id_pla
                request.session['limite'] = planificacion.limite_actividades

                messages.success(request, "✅ Planificación registrada correctamente.")
                return redirect('ver_grupo_por_cedula')
            else:
                messages.error(request, "❌ No se encontró grupo asignado para este profesor.")
        else:
            messages.error(request, "❌ Ocurrió un error al registrar la planificación.")

    # ------------------------------------------
    # Paso 2: Registrar actividades si hay planificación en sesión
    # ------------------------------------------
    if 'planificacion_id' in request.session:
        try:
            planificacion = Planificacion.objects.get(id_pla=request.session['planificacion_id'])
        except Planificacion.DoesNotExist:
            request.session.pop('planificacion_id', None)
            request.session.pop('limite', None)
        else:
            limite = request.session.get('limite', 0)

            ActividadFormSet = modelformset_factory(
                Actividad,
                form=ActividadForm,
                extra=limite,
                max_num=limite,
                validate_max=True,
                can_delete=False
            )

            if request.method == 'POST' and 'form-TOTAL_FORMS' in request.POST:
                actividad_forms = ActividadFormSet(
                    request.POST,
                    queryset=Actividad.objects.none(),
                    form_kwargs={'user': request.user}
                )

                # Asignar relaciones antes de validar
                for form in actividad_forms:
                    if form.has_changed():  # Evita forms vacíos
                        form.instance.id_pla = planificacion
                        form.instance.id_g = planificacion.id_g

                if actividad_forms.is_valid():
                    for form in actividad_forms:
                        if form.cleaned_data:
                            form.save()

                    request.session.pop('planificacion_id', None)
                    request.session.pop('limite', None)
                    messages.success(request, "✅ Actividades registradas correctamente.")
                    return redirect('ver_grupo_por_cedula')
                else:
                    mostrar_form_actividades = True
                    messages.error(request, "❌ Ocurrió un error al registrar las actividades.")
            else:
                actividad_forms = ActividadFormSet(
                    queryset=Actividad.objects.none(),
                    form_kwargs={'user': request.user}
                )
                mostrar_form_actividades = True

    # ------------------------------------------
    # Mostrar planificaciones y actividades
    # ------------------------------------------
    if grupo_asignado:
        planificaciones = Planificacion.objects.filter(id_g=grupo_asignado.id_g)
        actividades = Actividad.objects.filter(id_pla__in=planificaciones)

    return render(request, 'Planificacion/consultargrupo.html', {
        'grupo_asignado': grupo_asignado,
        'anio_escolar': anio_activo,
        'planificaciones': planificaciones,
        'actividades': actividades,
        'planificacion_form': planificacion_form,
        'actividad_forms': actividad_forms,
        'mostrar_form_actividades': mostrar_form_actividades,
        'planificacion': planificacion,
    })

# listado de planificacion con sus actividades 
@never_cache
@login_required
def listar_planificaciones(request):
    cedula_profesor = request.user.username
    anio_activo = AnioEscolar.objects.filter(activo=True).first()

    if not anio_activo:
        messages.error(request, 'No hay un año escolar activo configurado.')
        return redirect('ver_grupo_por_cedula')

    grupo_asignado = Horario.objects.filter(
        cedula_profesor=cedula_profesor,
        id_ano=anio_activo
    ).first()

    if not grupo_asignado:
        messages.warning(request, 'No se encontró grupo asignado para este profesor.')
        return redirect('ver_grupo_por_cedula')

    planificaciones = Planificacion.objects.filter(id_g=grupo_asignado.id_g).order_by('-id_pla')
    actividades_por_planificacion = {
        p: Actividad.objects.filter(id_pla=p).order_by('id_act') for p in planificaciones
    }

    return render(request, 'Planificacion/listar_planificaciones.html', {
        'grupo_asignado': grupo_asignado,
        'anio_escolar': anio_activo,
        'planificaciones': planificaciones,
        'actividades_por_planificacion': actividades_por_planificacion,
    })

@require_POST
@login_required
def cambiar_estado_actividad(request, actividad_id):
    actividad = get_object_or_404(Actividad, id_act=actividad_id)

    if request.method == "POST":
        actividad.evaluada = not actividad.evaluada
        actividad.save()
        estado = "evaluada" if actividad.evaluada else "no evaluada"
        messages.success(request, f"La actividad fue marcada como {estado}.")
    
    return redirect('listar_planificaciones')




#------------------------------ X GRUPO ------------------------------#

@login_required
def ver_estudiantes_por_grupo(request):
    # Obtener la cédula del profesor autenticado
    cedula_profesor = request.user.username  # Asegúrate de que este campo sea correcto

    # Obtener el año escolar activo
    anio_activo = AnioEscolar.objects.filter(activo=True).first()

    if not anio_activo:
        return render(request, 'Estudiante/consultar_estudiantes.html', {
            'error': 'No hay un año escolar activo configurado.'
        })

    # Buscar el horario del profesor en el año activo
    grupo_asignado = Horario.objects.filter(
        cedula_profesor=cedula_profesor,
        id_ano=anio_activo
    ).first()

    # Verificar si se encontró un grupo asignado
    if grupo_asignado:
        # Buscar estudiantes inscritos en ese grupo y en el año escolar activo
        estudiantes_inscritos = Inscripcion.objects.filter(
            id_g=grupo_asignado.id_g,
            id_ano=anio_activo
        )
    else:
        estudiantes_inscritos = []

    return render(request, 'Estudiante/consultar_estudiantes.html', {
        'grupo_asignado': grupo_asignado,
        'estudiantes_inscritos': estudiantes_inscritos
    })

#------------------------------ NOTAS ------------------------------#

# @login_required
# def ver_estudiantes_por_grupo_notas(request):
#     cedula_profesor = request.user.username
#     notas = []

#     # Año escolar activo
#     anio_activo = AnioEscolar.objects.filter(activo=True).first()
#     if not anio_activo:
#         messages.error(request, '❌ No hay un año escolar activo configurado.')
#         return render(request, 'Estudiante/estudiante_notas.html', {
#             'grupo_asignado': None,
#             'notas': notas
#         })

#     # Grupo asignado al profesor
#     grupo_asignado = Horario.objects.filter(
#         cedula_profesor=cedula_profesor,
#         id_ano=anio_activo
#     ).first()
#     if not grupo_asignado:
#         messages.warning(request, '⚠️ No tiene un grupo asignado para el año escolar activo.')
#         return render(request, 'Estudiante/estudiante_notas.html', {
#             'grupo_asignado': None,
#             'notas': notas
#         })

#     # Estudiantes inscritos
#     inscripciones = Inscripcion.objects.filter(
#         id_g=grupo_asignado.id_g,
#         id_ano=anio_activo
#     )

#     errores = False

#     if request.method == 'POST':
#         for inscripcion in inscripciones:
#             nota, _ = Nota.objects.get_or_create(id_inscripcion=inscripcion)
#             form = NotaForm(request.POST, instance=nota, prefix=str(inscripcion.pk))

#             if form.is_valid():
#                 nota = form.save(commit=False)
#                 nota.fecha_actualizacion = timezone.now()
#                 nota.save()
#             else:
#                 errores = True

#             notas.append({'inscripcion': inscripcion, 'form': form})

#         if errores:
#             messages.error(request, "❌ Algunas notas no se pudieron guardar.")
#         else:
#             messages.success(request, '✅ Notas actualizadas correctamente.')
#             return redirect('consultar_estudiantes_notas')

#     else:
#         for inscripcion in inscripciones:
#             nota, created = Nota.objects.get_or_create(id_inscripcion=inscripcion)
#             if created:
#                 nota.fecha_registro = timezone.now()
#                 nota.save()
#             form = NotaForm(instance=nota, prefix=str(inscripcion.pk))
#             notas.append({'inscripcion': inscripcion, 'form': form})

#     return render(request, 'Estudiante/estudiante_notas.html', {
#         'grupo_asignado': grupo_asignado,
#         'notas': notas
#     })


@login_required
def ver_estudiantes_por_grupo_notas(request):
    cedula_profesor = request.user.username
    notas = []

    anio_activo = AnioEscolar.objects.filter(activo=True).first()
    if not anio_activo:
        messages.error(request, '❌ No hay un año escolar activo configurado.')
        return render(request, 'Estudiante/estudiante_notas.html', {'grupo_asignado': None, 'notas': notas})

    grupo_asignado = Horario.objects.filter(cedula_profesor=cedula_profesor, id_ano=anio_activo).first()
    if not grupo_asignado:
        messages.warning(request, '⚠️ No tiene un grupo asignado para el año escolar activo.')
        return render(request, 'Estudiante/estudiante_notas.html', {'grupo_asignado': None, 'notas': notas})

    inscripciones = Inscripcion.objects.filter(id_g=grupo_asignado.id_g, id_ano=anio_activo)

    mes_actual = timezone.now().month
    lapso_actual = None
    if mes_actual == 12:
        lapso_actual = 'corte_1'
    elif mes_actual == 4:
        lapso_actual = 'corte_2'
    elif mes_actual == 6:
        lapso_actual = 'corte_3'

    if request.method == 'POST':
        exito = True
        for inscripcion in inscripciones:
            nota, _ = Nota.objects.get_or_create(id_inscripcion=inscripcion)
            prefix = str(inscripcion.pk)

            # Obtener datos POST solo del formulario actual
            form_data = {key: value for key, value in request.POST.items() if key.startswith(f"{prefix}-")}

            # Agregar manualmente valores de campos disabled para que estén en form_data
            if lapso_actual != 'corte_1':
                form_data[f"{prefix}-corte_1"] = str(nota.corte_1 or '')
            if lapso_actual != 'corte_2':
                form_data[f"{prefix}-corte_2"] = str(nota.corte_2 or '')
            if lapso_actual != 'corte_3':
                form_data[f"{prefix}-corte_3"] = str(nota.corte_3 or '')

            form = NotaForm(form_data, instance=nota, prefix=prefix, lapso_actual=lapso_actual)

            if form.is_valid():
                if lapso_actual:
                    nuevo_valor = form.cleaned_data.get(lapso_actual)
                    if nuevo_valor is not None:
                        setattr(nota, lapso_actual, nuevo_valor)
                        nota.fecha_actualizacion = timezone.now()
                        nota.save(update_fields=[lapso_actual, 'fecha_actualizacion'])
                    else:
                        messages.warning(
                            request,
                            f"⚠️ El campo {lapso_actual.replace('_', ' ').title()} está vacío para "
                            f"{inscripcion.nombre_estudiante} {inscripcion.apellido_estudiante}."
                        )
                        exito = False
                else:
                    messages.error(request, "❌ No se puede determinar el lapso actual.")
                    exito = False
            else:
                exito = False
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"❌ Error en {field} para {inscripcion.nombre_estudiante}: {error}")

        if exito:
            messages.success(request, '✅ Notas actualizadas correctamente.')
        else:
            messages.error(request, '❌ Hubo errores al guardar algunas notas.')

        return redirect('consultar_estudiantes_notas')

    else:
        for inscripcion in inscripciones:
            nota, created = Nota.objects.get_or_create(id_inscripcion=inscripcion)
            if created:
                nota.fecha_registro = timezone.now()
                nota.save()

            form = NotaForm(instance=nota, prefix=str(inscripcion.pk), lapso_actual=lapso_actual)

            # Desactivar campos que no corresponden al lapso actual con disabled
            if lapso_actual != 'corte_1':
                form.fields['corte_1'].widget.attrs['disabled'] = True
            if lapso_actual != 'corte_2':
                form.fields['corte_2'].widget.attrs['disabled'] = True
            if lapso_actual != 'corte_3':
                form.fields['corte_3'].widget.attrs['disabled'] = True

            notas.append({'inscripcion': inscripcion, 'form': form})

    return render(request, 'Estudiante/estudiante_notas.html', {
        'grupo_asignado': grupo_asignado,
        'notas': notas,
        'lapso_actual': lapso_actual
    })


#------------------------------ registrar ------------------------------#
@login_required
def ver_estudiantes_por_grupo_asistencia(request):
    cedula_profesor = request.user.username
    asistencias = []

    anio_activo = AnioEscolar.objects.filter(activo=True).first()
    if not anio_activo:
        messages.error(request, '❌ No hay un año escolar activo configurado.')
        return render(request, 'Estudiante/estudiante_asistencia.html', {
            'grupo_asignado': None,
            'asistencias': asistencias
        })

    grupo_asignado = Horario.objects.filter(
        cedula_profesor=cedula_profesor,
        id_ano=anio_activo
    ).first()
    if not grupo_asignado:
        messages.warning(request, '⚠️ No tiene un grupo asignado para el año escolar activo.')
        return render(request, 'Estudiante/estudiante_asistencia.html', {
            'grupo_asignado': None,
            'asistencias': asistencias
        })

    inscripciones = Inscripcion.objects.filter(
        id_g=grupo_asignado.id_g,
        id_ano=anio_activo
    )

    if request.method == 'POST':
        if 'eliminar_todo' in request.POST:
            Asistencia.objects.filter(
                id_g=grupo_asignado.id_g,
                id_estudiante__in=inscripciones
            ).delete()
            messages.success(request, "✅ Todas las asistencias del grupo han sido eliminadas.")
            return redirect('consultar_estudiantes_asistencia')

        if 'eliminar_encuentro' in request.POST:
            numero_encuentro = request.POST.get('numero_encuentro_eliminar')
            if numero_encuentro and numero_encuentro.isdigit():
                Asistencia.objects.filter(
                    id_g=grupo_asignado.id_g,
                    id_estudiante__in=inscripciones,
                    encuentro_numero=int(numero_encuentro)
                ).delete()
                messages.success(request, f"✅ Encuentro {numero_encuentro} eliminado correctamente.")
            else:
                messages.error(request, "❌ Número de encuentro inválido.")
            return redirect('consultar_estudiantes_asistencia')

        for inscripcion in inscripciones:
            num_encuentros = Asistencia.objects.filter(id_estudiante=inscripcion).count()

            for i in range(1, num_encuentros + 1):
                asistencia, _ = Asistencia.objects.get_or_create(
                    id_estudiante=inscripcion,
                    id_g=grupo_asignado.id_g,
                    encuentro_numero=i
                )
                asistio = request.POST.get(f"asistencia_{inscripcion.pk}_{i}") == 'on'
                fecha = request.POST.get(f"fecha_{inscripcion.pk}_{i}")

                if fecha:
                    try:
                        fecha_parsed = datetime.strptime(fecha, "%Y-%m-%d").date()
                        if fecha_parsed > timezone.now().date():
                            messages.error(request, f"❌ Fecha futura no permitida para {inscripcion.nombre_estudiante} en el encuentro {i}.")
                            return redirect('consultar_estudiantes_asistencia')
                        asistencia.fecha_encuentro = fecha_parsed
                    except ValueError:
                        messages.error(request, f"❌ Formato de fecha inválido para {inscripcion.nombre_estudiante} en el encuentro {i}.")
                        return redirect('consultar_estudiantes_asistencia')
                else:
                    asistencia.fecha_encuentro = None

                asistencia.asistio = asistio
                asistencia.save()

            for key in request.POST:
                if key.startswith(f"fecha_{inscripcion.pk}_"):
                    encuentro_numero = key.split('_')[-1]
                    asistencia, _ = Asistencia.objects.get_or_create(
                        id_estudiante=inscripcion,
                        id_g=grupo_asignado.id_g,
                        encuentro_numero=encuentro_numero
                    )
                    asistio = request.POST.get(f"asistencia_{inscripcion.pk}_{encuentro_numero}") == 'on'
                    fecha = request.POST.get(f"fecha_{inscripcion.pk}_{encuentro_numero}")

                    if fecha:
                        try:
                            fecha_parsed = datetime.strptime(fecha, "%Y-%m-%d").date()
                            if fecha_parsed > timezone.now().date():
                                messages.error(request, f"❌ Fecha futura no permitida para {inscripcion.nombre_estudiante} en el encuentro {encuentro_numero}.")
                                return redirect('consultar_estudiantes_asistencia')
                            asistencia.fecha_encuentro = fecha_parsed
                        except ValueError:
                            messages.error(request, f"❌ Formato de fecha inválido para {inscripcion.nombre_estudiante} en el encuentro {encuentro_numero}.")
                            return redirect('consultar_estudiantes_asistencia')
                    else:
                        asistencia.fecha_encuentro = None

                    asistencia.asistio = asistio
                    asistencia.save()

        messages.success(request, '✅ Asistencias registradas o actualizadas correctamente.')
        return redirect('consultar_estudiantes_asistencia')

    for inscripcion in inscripciones:
        encuentros = Asistencia.objects.filter(
            id_estudiante=inscripcion,
            id_g=grupo_asignado.id_g
        ).order_by('encuentro_numero')
        asistencias.append({'inscripcion': inscripcion, 'encuentros': encuentros})

    return render(request, 'Estudiante/estudiante_asistencia.html', {
        'grupo_asignado': grupo_asignado,
        'asistencias': asistencias
    })


#------------------------------ pdf ------------------------------#






#------------------------------ pdf ------------------------------# 



#------------------------------ pdf ------------------------------#
# PDF estudiante comienzo


@login_required
def generar_reporte_pdf(request):
    # Obtener la cédula del profesor autenticado
    cedula_profesor = request.user.username

    # Obtener el año escolar activo
    anio_activo = AnioEscolar.objects.filter(activo=True).first()

    if not anio_activo:
        return HttpResponse("No hay un año escolar activo configurado.", content_type="text/plain")

    # Buscar el grupo asignado al profesor en el año escolar activo
    grupo_asignado = Horario.objects.filter(
        cedula_profesor=cedula_profesor,
        id_ano=anio_activo
    ).first()

    # Comenzar generación de PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_estudiantes.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)
    elementos = []
    styles = getSampleStyleSheet()

    # Logos
    imagen_izquierda = "http://localhost:8000/static/images/bg.png"
    imagen_derecha = "http://localhost:8000/static/images/lg.png"

    img_left = Image(imagen_izquierda, width=1*inch, height=1*inch)
    img_right = Image(imagen_derecha, width=1*inch, height=1*inch)

    header_table = Table(
        [[img_left, '', img_right]],
        colWidths=[2*inch, 3.5*inch, 2*inch]
    )
    header_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    elementos.append(header_table)
    elementos.append(Spacer(1, 10))

    liceo_style = ParagraphStyle(
        name='NombreLiceo',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=12
    )
    nombre_liceo = Paragraph("<b>Complejo Educativo Dr. César Lizardo</b>", liceo_style)
    elementos.append(nombre_liceo)

    nombre_grupo = grupo_asignado.nombre_grupo if grupo_asignado else "Sin Grupo Asignado"

    titulo_style = ParagraphStyle(
        name='TituloCentrado',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=14,
        spaceAfter=6
    )

    titulo_texto = f"<b>Estudiantes Inscritos - Grupo: {nombre_grupo}</b>"
    titulo = Paragraph(titulo_texto, titulo_style)
    elementos.append(titulo)

    # Aquí agregamos el nombre completo del profesor justo debajo del título
    nombre_completo_profesor = (
        f"{grupo_asignado.tipo_cedula_profesor}{grupo_asignado.cedula_profesor} {grupo_asignado.nombre_profesor} {grupo_asignado.apellido_profesor}"
        if grupo_asignado else "Profesor no asignado"
    )
    profesor_style = ParagraphStyle(
        name='ProfesorNombre',
        parent=styles['Normal'],
        alignment=TA_LEFT,
        fontSize=12,
        spaceBefore=15,
        leftIndent=10,  
        spaceAfter=20,
    )
    parrafo_profesor = Paragraph(f"<b>Profesor: {nombre_completo_profesor}</b>", profesor_style)
    elementos.append(parrafo_profesor)

    data = [['#', 'Cédula', 'Nombres', 'Apellidos', 'Año Cursante', 'Sección']]

    if grupo_asignado:
        estudiantes_inscritos = Inscripcion.objects.filter(
            id_g=grupo_asignado.id_g,
            id_ano=anio_activo
        )
    else:
        estudiantes_inscritos = []

    for idx, estudiante in enumerate(estudiantes_inscritos, start=1):
        cedula_completa = f"{estudiante.tipo_cedula_estudiante}{estudiante.cedula_estudiante}"
        data.append([
            idx,
            cedula_completa,
            estudiante.nombre_estudiante,
            estudiante.apellido_estudiante,
            estudiante.ano_curso,
            estudiante.seccion
        ])

    table = Table(data, repeatRows=1, hAlign='CENTER')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#004c99")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elementos.append(table)

    doc.build(elementos, canvasmaker=NumberedCanvas)

    return response


# PDF estudiante fin
# PDF DE NOTAS 
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()  # Corrección importante

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(total_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, total_pages):
        self.setFont("Helvetica", 9)
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")  # ✅ Corregido aquí
        self.drawString(20 * mm, 10 * mm, f"Descargado el: {fecha_actual}")
        self.drawRightString(200 * mm, 10 * mm, f"Página {self._pageNumber} de {total_pages}")

# PDF NOTAS
@login_required
def exportar_notas_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="notas_estudiantes.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)
    elementos = []
    styles = getSampleStyleSheet()

    titulo_centrado_style = ParagraphStyle(
        name='TituloCentrado',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=10,
        spaceAfter=10
    )

    # Logos
    img_left = Image("http://localhost:8000/static/images/bg.png", width=1*inch, height=1*inch)
    img_right = Image("http://localhost:8000/static/images/lg.png", width=1*inch, height=1*inch)

    header_table = Table(
        [[img_left, '', img_right]],
        colWidths=[2*inch, 3.5*inch, 2*inch]
    )
    header_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elementos.append(header_table)
    elementos.append(Spacer(1, 10))

    liceo_nombre = Paragraph('<b style="font-size:18px;">Complejo Educativo Dr. César Lizardo</b>', styles['Title'])
    elementos.append(liceo_nombre)
    elementos.append(Spacer(1, 8))

    # Año escolar activo
    anio_activo = AnioEscolar.objects.filter(activo=True).first()
    if not anio_activo:
        elementos.append(Paragraph("❌ No hay un año escolar activo configurado.", styles['Normal']))
        doc.build(elementos)
        return response

    # Grupo asignado al profesor
    cedula_profesor = request.user.username
    grupo_asignado = Horario.objects.filter(
        cedula_profesor=cedula_profesor,
        id_ano=anio_activo
    ).first()
    if not grupo_asignado:
        elementos.append(Paragraph("⚠️ No tiene un grupo asignado para el año escolar activo.", styles['Normal']))
        doc.build(elementos)
        return response

    nombre_grupo = grupo_asignado.nombre_grupo
    anio_escolar_nombre = anio_activo.nombreano

    # Título principal
    titulo_texto = f"<b>Listado de Notas - Grupo: {nombre_grupo} - Año Escolar: {anio_escolar_nombre}</b>"
    titulo_seccion = Paragraph(titulo_texto, titulo_centrado_style)
    elementos.append(titulo_seccion)
    elementos.append(Spacer(1, 8))

    # Datos del profesor
    datos_profesor = (
        f"<b>Profesor:</b> {grupo_asignado.tipo_cedula_profesor}"
        f"{grupo_asignado.cedula_profesor} - "
        f"{grupo_asignado.nombre_profesor} {grupo_asignado.apellido_profesor}"
    )
    parrafo_profesor = Paragraph(datos_profesor, styles['Normal'])
    elementos.append(parrafo_profesor)
    elementos.append(Spacer(1, 12))

    # Notas del grupo
    notas = Nota.objects.select_related('id_inscripcion').filter(
        id_inscripcion__id_g=grupo_asignado.id_g,
        id_inscripcion__id_ano=anio_activo
    )

    if not notas.exists():
        elementos.append(Paragraph("⚠️ No hay notas registradas para este grupo y año escolar.", styles['Normal']))
        doc.build(elementos)
        return response

    # Encabezado de tabla
    data = [['#', 'Cédula', 'Nombre', 'Apellido', '1er Lapso', '2do Lapso', '3er Lapso', 'Promedio', 'Literal']]

    def calcular_literal(promedio):
        if promedio == "N/R":
            return "N/R"
        if 18 <= promedio <= 20:
            return "A"
        elif 15 <= promedio <= 17:
            return "B"
        elif 10 <= promedio <= 14:
            return "C"
        elif 1 <= promedio <= 9:
            return "D"
        else:
            return "N/R"

    for idx, nota in enumerate(notas, start=1):
        estudiante = nota.id_inscripcion
        cedula = f"{estudiante.tipo_cedula_estudiante}{estudiante.cedula_estudiante}"

        cortes = [nota.corte_1, nota.corte_2, nota.corte_3]
        notas_validas = [n for n in cortes if n is not None]
        promedio = round(sum(notas_validas) / len(notas_validas)) if notas_validas else "N/R"
        literal = calcular_literal(promedio)

        data.append([
            idx,
            cedula,
            estudiante.nombre_estudiante,
            estudiante.apellido_estudiante,
            nota.corte_1 if nota.corte_1 is not None else "N/R",
            nota.corte_2 if nota.corte_2 is not None else "N/R",
            nota.corte_3 if nota.corte_3 is not None else "N/R",
            promedio,
            literal,
        ])

    table = Table(data, repeatRows=1, hAlign='CENTER',
                  colWidths=[25, 75, 75, 75, 50, 50, 50, 60, 45])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#004c99")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('FONTSIZE', (0,1), (-1,-1), 7),  # Contenido estudiantes
        ('BOTTOMPADDING', (0,0), (-1,0), 2),
        ('BOTTOMPADDING', (0,1), (-1,-1), 2),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))

    elementos.append(table)
    doc.build(elementos, canvasmaker=NumberedCanvas)

    return response
#------------------------------ pdf ------------------------------#


#------------------------------ pdf ------------------------------#
@login_required
def generar_pdf_por_sexo(request, sexo, nombre_archivo):
    anio_activo = AnioEscolar.objects.filter(activo=True).first()
    if not anio_activo:
        return HttpResponse("No hay un año escolar activo configurado.", content_type="text/plain")

    inscripciones = Inscripcion.objects.filter(id_ano=anio_activo).select_related('id_estudiante')
    
    # Filtrar por sexo del estudiante
    if sexo == 'masculino':
        inscripciones = [i for i in inscripciones if i.id_estudiante.Sexo.lower().startswith('m')]
    else:
        inscripciones = [i for i in inscripciones if i.id_estudiante.Sexo.lower().startswith('f')]

    # Agrupar por nombre_grupo
    grupos = {}
    for insc in inscripciones:
        grupos.setdefault(insc.nombre_grupo, []).append(insc)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'

    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)

    elementos = []
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        name='TituloCentrado',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=12,
        spaceAfter=14
    )

    # Encabezado
    img_left = Image("http://localhost:8000/static/images/bg.png", width=1*inch, height=1*inch)
    img_right = Image("http://localhost:8000/static/images/lg.png", width=1*inch, height=1*inch)
    header_table = Table([[img_left, '', img_right]], colWidths=[2*inch, 3.5*inch, 2*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elementos.append(header_table)
    elementos.append(Spacer(1, 12))

    titulo = f"<b>Listado de Estudiantes {'Masculinos' if sexo == 'masculino' else 'Femeninas'}</b>"
    elementos.append(Paragraph(titulo, titulo_style))

    periodo = Paragraph(f"<b>Año Escolar: {anio_activo.nombreano}</b>", styles['Heading3'])
    elementos.append(periodo)
    elementos.append(Spacer(1, 12))

    for nombre_grupo, estudiantes in grupos.items():
        titulo_grupo = Paragraph(f"<b>Grupo de Interés: {nombre_grupo}</b>", styles['Heading4'])
        elementos.append(titulo_grupo)
        elementos.append(Spacer(1, 8))

        data = [['#', 'Cédula', 'Nombres', 'Apellidos', 'Año', 'Sección']]
        for idx, est in enumerate(estudiantes, start=1):
            cedula = f"{est.tipo_cedula_estudiante}{est.cedula_estudiante}"
            data.append([
                idx,
                cedula,
                est.nombre_estudiante,
                est.apellido_estudiante,
                est.ano_curso,
                est.seccion
            ])

        table = Table(data, repeatRows=1, hAlign='CENTER', colWidths=[30, 90, 100, 100, 70, 60])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#004c99")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ]))
        elementos.append(table)
        elementos.append(Spacer(1, 20))

    doc.build(elementos, canvasmaker=NumberedCanvas)
    return response

#------------------------------ pdf ------------------------------#
@login_required
def exportar_estudiantes_masculinos_pdf(request):
    return generar_pdf_por_sexo(request, sexo='masculino', nombre_archivo="estudiantes_masculinos_por_grupo.pdf")
#------------------------------ pdf ------------------------------#
@login_required
def exportar_estudiantes_femeninas_pdf(request):
    return generar_pdf_por_sexo(request, sexo='femenino', nombre_archivo="estudiantes_femeninas_por_grupo.pdf")
#------------------------------ pdf ------------------------------#

@login_required
def exportar_notas_pdff(request, lapso):
    LAPSO_MAP = {
        "1": ("1er Lapso", "corte_1"),
        "2": ("2do Lapso", "corte_2"),
        "3": ("3er Lapso", "corte_3"),
    }

    if lapso not in LAPSO_MAP:
        return HttpResponse("Lapso inválido.", status=400)

    lapso_nombre, campo_nota = LAPSO_MAP[lapso]

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="notas_{lapso_nombre.replace(" ", "_").lower()}.pdf"'

    doc = SimpleDocTemplate(
        response, 
        pagesize=letter,
        rightMargin=30, leftMargin=30,
        topMargin=30, bottomMargin=30
    )
    elementos = []
    styles = getSampleStyleSheet()

    titulo_centrado_style = ParagraphStyle(
        name='TituloCentrado',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=10,
        spaceAfter=10
    )

    # Logos
    img_left = Image("http://localhost:8000/static/images/bg.png", width=1*inch, height=1*inch)
    img_right = Image("http://localhost:8000/static/images/lg.png", width=1*inch, height=1*inch)

    header_table = Table(
        [[img_left, '', img_right]],
        colWidths=[2*inch, 3.5*inch, 2*inch]
    )
    header_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elementos.append(header_table)
    elementos.append(Spacer(1, 10))

    liceo_nombre = Paragraph(
        '<b style="font-size:18px;">Complejo Educativo Dr. César Lizardo</b>', 
        styles['Title']
    )
    elementos.append(liceo_nombre)
    elementos.append(Spacer(1, 8))

    anio_activo = AnioEscolar.objects.filter(activo=True).first()
    if not anio_activo:
        elementos.append(Paragraph("❌ No hay un año escolar activo configurado.", styles['Normal']))
        doc.build(elementos)
        return response

    cedula_profesor = request.user.username
    grupo_asignado = Horario.objects.filter(
        cedula_profesor=cedula_profesor,
        id_ano=anio_activo
    ).first()
    if not grupo_asignado:
        elementos.append(Paragraph("⚠️ No tiene un grupo asignado para el año escolar activo.", styles['Normal']))
        doc.build(elementos)
        return response

    titulo_texto = f"<b>Notas del {lapso_nombre} - Grupo: {grupo_asignado.nombre_grupo} - Año: {anio_activo.nombreano}</b>"
    elementos.append(Paragraph(titulo_texto, titulo_centrado_style))
    elementos.append(Spacer(1, 8))

    datos_profesor = (
        f"<b>Profesor:</b> {grupo_asignado.tipo_cedula_profesor}"
        f"{grupo_asignado.cedula_profesor} - "
        f"{grupo_asignado.nombre_profesor} {grupo_asignado.apellido_profesor}"
    )
    elementos.append(Paragraph(datos_profesor, styles['Normal']))
    elementos.append(Spacer(1, 12))

    notas = Nota.objects.select_related('id_inscripcion').filter(
        id_inscripcion__id_g=grupo_asignado.id_g,
        id_inscripcion__id_ano=anio_activo
    )

    if not notas.exists():
        elementos.append(Paragraph(f"⚠️ No hay notas registradas para el {lapso_nombre}.", styles['Normal']))
        doc.build(elementos)
        return response

    def calcular_literal(nota):
        if nota is None:
            return "N/R"
        if 18 <= nota <= 20:
            return "A"
        elif 15 <= nota <= 17:
            return "B"
        elif 10 <= nota <= 14:
            return "C"
        elif 1 <= nota <= 9:
            return "D"
        else:
            return "N/R"

    data = [['#', 'Cédula', 'Nombre', 'Apellido', lapso_nombre, 'Literal']]

    for idx, nota in enumerate(notas, start=1):
        estudiante = nota.id_inscripcion
        cedula = f"{estudiante.tipo_cedula_estudiante}{estudiante.cedula_estudiante}"
        valor_lapso = getattr(nota, campo_nota)
        literal = calcular_literal(valor_lapso)
        data.append([
            idx,
            cedula,
            estudiante.nombre_estudiante,
            estudiante.apellido_estudiante,
            valor_lapso if valor_lapso is not None else "N/R",
            literal,
        ])

    table = Table(
        data, repeatRows=1, hAlign='CENTER',
        colWidths=[25, 75, 75, 75, 60, 45]
    )

    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#004c99")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('FONTSIZE', (0,1), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,0), 2),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))

    elementos.append(table)
    elementos.append(Spacer(1, 12))

    leyenda_texto = """
    <b>Leyenda de Literales:</b><br/>
    A: 18-20<br/>
    B: 15-17<br/>
    C: 10-14<br/>
    D: 1-9<br/>
    N/R: No registrado o inválido
    """
    leyenda = Paragraph(leyenda_texto, ParagraphStyle(
        name='Leyenda',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        alignment=TA_CENTER,
        spaceBefore=10,
        spaceAfter=0,
        textColor=colors.black,
    ))
    elementos.append(leyenda)

    doc.build(elementos, canvasmaker=NumberedCanvas)

    return response



#------------------------------ pdf ------------------------------#
@login_required
def exportar_estudiantes_general_pdf(request):
    # Año escolar activo
    anio_activo = AnioEscolar.objects.filter(activo=True).first()
    if not anio_activo:
        return HttpResponse("No hay un año escolar activo configurado.", content_type="text/plain")

    inscripciones = Inscripcion.objects.filter(id_ano=anio_activo).order_by('nombre_grupo', 'apellido_estudiante')

    # Agrupar por nombre_grupo
    grupos = {}
    for insc in inscripciones:
        grupos.setdefault(insc.nombre_grupo, []).append(insc)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="estudiantes_grupos_general.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)

    elementos = []
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        name='TituloCentrado',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=12,
        spaceAfter=14
    )

    # Logos
    img_left = Image("http://localhost:8000/static/images/bg.png", width=1*inch, height=1*inch)
    img_right = Image("http://localhost:8000/static/images/lg.png", width=1*inch, height=1*inch)

    header_table = Table([[img_left, '', img_right]], colWidths=[2*inch, 3.5*inch, 2*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elementos.append(header_table)
    elementos.append(Spacer(1, 12))

    liceo = Paragraph("<b>Complejo Educativo Dr. César Lizardo</b>", titulo_style)
    elementos.append(liceo)

    periodo = Paragraph(f"<b>Año Escolar: {anio_activo.nombreano}</b>", styles['Heading3'])
    elementos.append(periodo)
    elementos.append(Spacer(1, 12))

    for nombre_grupo, estudiantes in grupos.items():
        titulo_grupo = Paragraph(f"<b>Grupo de Interés: {nombre_grupo}</b>", styles['Heading4'])
        elementos.append(titulo_grupo)
        elementos.append(Spacer(1, 8))

        data = [['#', 'Cédula', 'Nombres', 'Apellidos', 'Año', 'Sección']]

        for idx, est in enumerate(estudiantes, start=1):
            cedula = f"{est.tipo_cedula_estudiante}{est.cedula_estudiante}"
            data.append([
                idx,
                cedula,
                est.nombre_estudiante,
                est.apellido_estudiante,
                est.ano_curso,
                est.seccion
            ])

        table = Table(data, repeatRows=1, hAlign='CENTER', colWidths=[30, 90, 100, 100, 70, 60])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#004c99")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ]))
        elementos.append(table)
        elementos.append(Spacer(1, 20))

    doc.build(elementos, canvasmaker=NumberedCanvas)  # Si usas NumberedCanvas, añade: , canvasmaker=NumberedCanvas
    return response

#------------------------------ pdf ------------------------------#

@login_required
def exportar_profesores_grupo_pdf(request):
    # Obtener el año escolar activo
    anio_activo = AnioEscolar.objects.filter(activo=True).first()
    if not anio_activo:
        return HttpResponse("No hay un año escolar activo configurado.", content_type="text/plain")

    # Obtener los horarios asignados en el año escolar activo
    horarios = Horario.objects.filter(id_ano=anio_activo).order_by('nombre_grupo', 'apellido_profesor')

    # Agrupar por nombre_grupo
    grupos = {}
    for horario in horarios:
        grupos.setdefault(horario.nombre_grupo, []).append(horario)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="profesores_grupos_activos.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)

    elementos = []
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        name='TituloCentrado',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=12,
        spaceAfter=14
    )

    # Logos
    img_left = Image("http://localhost:8000/static/images/lg.png", width=1*inch, height=1*inch)
    img_right = Image("http://localhost:8000/static/images/bg.png", width=1*inch, height=1*inch)

    header_table = Table([[img_left, '', img_right]], colWidths=[2*inch, 3.5*inch, 2*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elementos.append(header_table)
    elementos.append(Spacer(1, 12))

    liceo = Paragraph("<b>Complejo Educativo Dr. César Lizardo</b>", titulo_style)
    elementos.append(liceo)

    periodo = Paragraph(f"<b>Año Escolar: {anio_activo.nombreano}</b>", styles['Heading3'])
    elementos.append(periodo)
    elementos.append(Spacer(1, 12))

    for nombre_grupo, profesores in grupos.items():
        titulo_grupo = Paragraph(f"<b>Grupo de Interés: {nombre_grupo}</b>", styles['Heading4'])
        elementos.append(titulo_grupo)
        elementos.append(Spacer(1, 8))

        data = [['#', 'Cédula', 'Nombres', 'Apellidos', 'Grupo', ' Inicio', ' Final']]

        for idx, prof in enumerate(profesores, start=1):
            cedula = f"{prof.tipo_cedula_profesor}{prof.cedula_profesor}"
            data.append([
                idx,
                cedula,
                prof.nombre_profesor,
                prof.apellido_profesor,
                prof.nombre_grupo,
                prof.hora_inicio.strftime("%H:%M"),
                prof.hora_final.strftime("%H:%M")
            ])

        table = Table(data, repeatRows=1, hAlign='CENTER', colWidths=[30, 75, 100, 100, 70, 50, 50])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#004c99")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elementos.append(table)
        elementos.append(Spacer(1, 20))

    doc.build(elementos,canvasmaker=NumberedCanvas)  # Si usas NumberedCanvas, añade: , canvasmaker=NumberedCanvas

    return response

#------------------------------ pdf ------------------------------#
@login_required
def exportar_asistencias_pdf(request):
    anio_activo = AnioEscolar.objects.filter(activo=True).first()
    if not anio_activo:
        return HttpResponse("No hay un año escolar activo configurado.", content_type="text/plain")

    cedula_profesor = request.user.username
    grupo_asignado = Horario.objects.filter(
        cedula_profesor=cedula_profesor,
        id_ano=anio_activo
    ).first()

    if not grupo_asignado:
        return HttpResponse("No tiene un grupo asignado para este año escolar.", content_type="text/plain")

    inscripciones = Inscripcion.objects.filter(
        id_g=grupo_asignado.id_g,
        id_ano=anio_activo
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="asistencias_estudiantes.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)

    elementos = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        name='TituloCentrado',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=10,
        spaceAfter=8
    )

    img_left = Image("http://localhost:8000/static/images/bg.png", width=1*inch, height=1*inch)
    img_right = Image("http://localhost:8000/static/images/lg.png", width=1*inch, height=1*inch)

    header_table = Table([[img_left, '', img_right]], colWidths=[2*inch, 3.5*inch, 2*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elementos.append(header_table)
    elementos.append(Spacer(1, 12))

    liceo = Paragraph("<b>Complejo Educativo Dr. César Lizardo</b>", titulo_style)
    elementos.append(liceo)

    periodo = Paragraph(f"<b>Año Escolar: {anio_activo.nombreano}</b>", styles['Heading3'])
    elementos.append(periodo)
    elementos.append(Spacer(1, 12))

    titulo_grupo = Paragraph(f"<b>Grupo de Interés: {grupo_asignado.nombre_grupo}</b>", styles['Heading4'])
    elementos.append(titulo_grupo)
    elementos.append(Spacer(1, 12))

    # Aquí agregamos el nombre del profesor
    nombre_profesor = f"{grupo_asignado.tipo_cedula_profesor} {grupo_asignado.cedula_profesor} - {grupo_asignado.nombre_profesor} {grupo_asignado.apellido_profesor}"
    profesor_paragraph = Paragraph(f"<b>Profesor: {nombre_profesor}</b>", styles['Normal'])
    elementos.append(profesor_paragraph)
    elementos.append(Spacer(1, 12))

    # Tabla de asistencias
    data = [['#', 'Cédula', 'Nombres', 'Apellidos', 'Encuentros', 'Asistencias', '% Asistencia']]

    for idx, inscripcion in enumerate(inscripciones, start=1):
        estudiante = inscripcion.id_estudiante
        asistencias = Asistencia.objects.filter(
            id_estudiante=inscripcion,
            id_g=grupo_asignado.id_g
        )

        total = asistencias.count()
        asistio = asistencias.filter(asistio=True).count()
        porcentaje = (asistio / total) * 100 if total > 0 else 0

        row = [
            idx,
            f"{inscripcion.tipo_cedula_estudiante}{inscripcion.cedula_estudiante}",
            estudiante.nombre_estudiante,
            estudiante.apellido_estudiante,
            total,
            asistio,
            f"{porcentaje:.1f}%"
        ]
        data.append(row)

    table = Table(data, repeatRows=1, hAlign='CENTER', colWidths=[30, 75, 100, 100, 60, 60, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#004c99")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elementos.append(table)
    doc.build(elementos, canvasmaker=NumberedCanvas)

    return response

#------------------------------ pdf ------------------------------#

@login_required
def exportar_grupos_disponibles_pdf(request):
    grupos_disponibles = Intere.objects.filter(status='DISPONIBLE')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="grupos_disponibles.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)

    elementos = []
    styles = getSampleStyleSheet()

    # Estilo título centrado
    titulo_style = ParagraphStyle(
        name='TituloCentrado',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=14,
        spaceAfter=14
    )

    # Encabezado con logos
    img_left = Image("http://localhost:8000/static/images/bg.png", width=1*inch, height=1*inch)
    img_right = Image("http://localhost:8000/static/images/lg.png", width=1*inch, height=1*inch)

    header_table = Table([[img_left, '', img_right]], colWidths=[2*inch, 3.5*inch, 2*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elementos.append(header_table)
    elementos.append(Spacer(1, 12))

    # Título principal
    titulo = Paragraph("<b>Grupos Disponibles</b>", titulo_style)
    elementos.append(titulo)
    elementos.append(Spacer(1, 12))

    # Tabla de grupos
    data = [['#', 'Nombre del Grupo', 'Descripción']]

    for idx, grupo in enumerate(grupos_disponibles, start=1):
        data.append([
            idx,
            grupo.nombre_grupo,
            grupo.descripcion_grupo or "Sin descripción"
        ])

    table = Table(data, repeatRows=1, hAlign='CENTER', colWidths=[30, 200, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#004c99")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elementos.append(table)
    doc.build(elementos,canvasmaker=NumberedCanvas)

    return response


#------------------------------ pdf ------------------------------#
#------------------------------ pdf ------------------------------#
@login_required
def calcular_literal(valor):
    if valor == "N/R":
        return "N/R"
    if 18 <= valor <= 20:
        return "A"
    elif 15 <= valor <= 17:
        return "B"
    elif 10 <= valor <= 14:
        return "C"
    elif 1 <= valor <= 9:
        return "D"
    else:
        return "N/R"

#------------------------------ PRUEBA ------------------------------#








#------------------------------ PRUEBA ------------------------------#
#------------------------------ PRUEBA ------------------------------#


    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    anio_activo = AnioEscolar.objects.filter(activo=True).first()
    if not anio_activo:
        return HttpResponse("No hay año escolar activo.", status=400)

    grupo_asignado = Horario.objects.filter(
        cedula_profesor=request.user.username,
        id_ano=anio_activo
    ).first()
    if not grupo_asignado:
        return HttpResponse("No tiene grupo asignado.", status=400)

    generar_pdf_por_corte(response, grupo_asignado, anio_activo, corte_num)
    return response

#------------------------------ PRUEBA ------------------------------#
@login_required
def gestionar_fechas_corte(request):
    # Obtener la única instancia o crearla si no existe
    instancia, creado = FechaCargaNota.objects.get_or_create(id_carganota=1)

    if request.method == 'POST':
        form = FechaCargaNotaForm(request.POST, instance=instancia)
        if form.is_valid():
            form.save()
            messages.success(request, "Fechas de carga de notas guardadas correctamente.")
            return redirect('gestionar_fechas_corte')  # Cambia por la URL que uses
        else:
            messages.error(request, "Por favor corrige los errores.")
    else:
        form = FechaCargaNotaForm(instance=instancia)

    return render(request, 'Planificacion/fecha_corte_form.html', {
        'form': form,
        'creado': creado,
    })
#------------------------------ PRUEBA ------------------------------#
#------------------------------ PRUEBA ------------------------------#

#------------------------------ Inscripciones ------------------------------#

class ListarInscripcion(View):
    model = Inscripcion

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(serialize('json', self.get_queryset()), 'application/json')
        else:
            return redirect('inicio_Inscripcion')

class BaseInscripcionView:
    def handle_ajax_response(self, mensaje, error, status_code):
        return JsonResponse({'mensaje': mensaje, 'error': error}, status=status_code)

        
class EditarInscripcion(UpdateView):
    model = Inscripcion
    form_class = InscripcionForm
    template_name = 'Inscripcion/editarInscripcion.html'
    context_object_name = 'inscripcion'
    
    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            inscripcion = self.get_object()
            context['inscripcion_data'] = {
                'id_estudiante': inscripcion.id_estudiante.id_estudiante,
                'seccion' : inscripcion.seccion,
                'ano_curso' : inscripcion.ano_curso,
                'id_ano' : inscripcion.id_ano.id_ano,
                'id_g': inscripcion.id_g.id_g,

            }
            return context
    
    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES ,instance = self.get_object())
            if form.is_valid():
                form.save()
                mensaje = f' La inscripcion se ha actualizado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f'La inscripcion no se ha podido actualizar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Inscripcion')



class RegistrarInscripcion(CreateView):
    model = Inscripcion
    form_class = InscripcionForm
    template_name = 'Inscripcion/registrarInscripcion.html'

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.form_class(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                mensaje = f' La Inscripcion de Interes se ha registrado correctamente'
                error = 'No hay error'
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 201
                return response
            else:
                mensaje = f' La Inscripcion se ha podido registrar'
                error = form.errors
                response = JsonResponse({'mensaje': mensaje, 'error': error})
                response.status_code = 400
                return response
        else:
            return redirect('inicio_Inscripcion')


class EliminarInscripcion(DeleteView):
    model = Inscripcion
    template_name = 'Inscripcion/eliminarInscripcion.html'
    success_url = reverse_lazy('inicio_Inscripcion')
    context_object_name = 'inscripcion'

    def delete(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            intere = self.get_object()
            intere.delete()
            mensaje = f'La inscripcion del estudiante se ha eliminado correctamente'
            error = 'No hay error'
            response = JsonResponse({'mensaje': mensaje, 'error': error})
            response.status_code = 201
            return response
        else:
            return redirect('inicio_Inscripcion')

class BuscarInscripciones(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        inscripciones = Intere.objects.filter(nombre_grupo__icontains=query)
        results = [{'id': inscripcion.id_inscripcion, 'text': f' {inscripcion.nombre_grupo}'} for inscripcion in inscripciones]
        return JsonResponse(results, safe=False)
    
       
#------------------------------ Inscripciones ------------------------------#


class ListarPlanificacion(View):
    model = Planificacion

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(serialize('json', self.get_queryset()), 'application/json')
        else:
            return redirect('inicio_Planificacion')



class EditarPlanificacion(UpdateView):
    model = Planificacion
    form_class = PlanificacionForm
    template_name = 'Planificacion/editarPlanificacion.html'
    context_object_name = 'planificacion'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        cedula_profesor = self.request.user.username
        anio_activo = AnioEscolar.objects.filter(activo=True).first()

        if anio_activo:
            grupos_asignados_ids = Horario.objects.filter(
                cedula_profesor=cedula_profesor,
                id_ano=anio_activo
            ).values_list('id_g__pk', flat=True)
            form.fields['id_g'].queryset = Intere.objects.filter(pk__in=grupos_asignados_ids)
        else:
            form.fields['id_g'].queryset = Intere.objects.none()

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cedula_profesor = self.request.user.username
        anio_activo = AnioEscolar.objects.filter(activo=True).first()

        if anio_activo:
            context['grupos'] = Horario.objects.filter(
                cedula_profesor=cedula_profesor,
                id_ano=anio_activo
            )
        else:
            context['grupos'] = []

        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.get_form()
            form.data = request.POST
            form.files = request.FILES
            form.instance = self.get_object()

            if form.is_valid():
                form.save()
                return JsonResponse({
                    'mensaje': 'La planificación se ha editado correctamente.',
                    'error': 'No hay error',
                    'redirect_url': reverse('consultargrupo')
                }, status=200)


            else:
                return JsonResponse({'mensaje': 'La Planificación no se ha podido actualizar', 'error': form.errors}, status=400)
        else:
            return redirect('ver_grupo_por_cedula')


class RegistrarPlanificacion(CreateView):
    model = Planificacion
    form_class = PlanificacionForm
    template_name = 'Planificacion/registrarPlanificacion.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        cedula_profesor = self.request.user.username
        anio_activo = AnioEscolar.objects.filter(activo=True).first()

        if anio_activo:
            grupos_asignados_ids = Horario.objects.filter(
                cedula_profesor=cedula_profesor,
                id_ano=anio_activo
            ).values_list('id_g__pk', flat=True)
            form.fields['id_g'].queryset = Intere.objects.filter(pk__in=grupos_asignados_ids)
        else:
            form.fields['id_g'].queryset = Intere.objects.none()

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cedula_profesor = self.request.user.username
        anio_activo = AnioEscolar.objects.filter(activo=True).first()

        if anio_activo:
            context['grupos'] = Horario.objects.filter(
                cedula_profesor=cedula_profesor,
                id_ano=anio_activo
            )
        else:
            context['grupos'] = []

        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.get_form()
            form.data = request.POST  # esto asegura que uses el mismo form con el queryset correcto
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'mensaje': 'La Planificación se ha registrado correctamente',
                    'error': 'No hay error',
                    'redirect_url': reverse('consultargrupo'),
                }, status=201)
            else:
                return JsonResponse({'mensaje': 'La Planificación no se ha podido registrar', 'error': form.errors}, status=400)
        else:
            return redirect('ver_grupo_por_cedula')


class EliminarPlanificacion(DeleteView):
    model = Planificacion
    template_name = 'Planificacion/eliminarPlanificacion.html'
    success_url = reverse_lazy('inicio_Planificacion')
    context_object_name = 'planificacion'

    def delete(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            planificacion = self.get_object()
            planificacion.delete()
            mensaje = f'La Planificacion se ha eliminado correctamente'
            error = 'No hay error'
            response = JsonResponse({'mensaje': mensaje, 'error': error})
            response.status_code = 201
            return response
        else:
            return redirect('ver_grupo_por_cedula')

class BuscarPlanificaciones(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        planificaciones = Planificacion.objects.filter(nombre_grupo__icontains=query)
        results = [{'id': Planificacion.id_g, 'text': f'{planificacion.nombre_pla}'} for planificacion in planificaciones]
        return JsonResponse(results, safe=False)
    
#------------------------------ Actividad ------------------------------#

#------------------------------ ESTA VISTA NO SIRVEEEEEEEEEEEEEE NO SIRVEEEEEEEEEEEEEEEE AIIUDAAAAAAAAAAAAAAAAAA ------------------------------#
class ListarActividad(View):
    model = Actividad

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(serialize('json', self.get_queryset()), 'application/json')
        else:
            return redirect('inicio_Actividad')

class EditarActividad(UpdateView):
    model = Actividad
    form_class = ActividadForm
    template_name = 'Actividad/editarActividad.html'
    context_object_name = 'actividad'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        cedula_profesor = self.request.user.username
        anio_activo = AnioEscolar.objects.filter(activo=True).first()

        if anio_activo:
            grupos_ids = Horario.objects.filter(
                cedula_profesor=cedula_profesor,
                id_ano=anio_activo
            ).values_list('id_g__pk', flat=True)
        else:
            grupos_ids = Intere.objects.none().values_list('pk', flat=True)

        form.fields['id_g'].queryset = Intere.objects.filter(pk__in=grupos_ids)
        form.fields['id_pla'].queryset = Planificacion.objects.filter(id_g__in=grupos_ids)

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cedula_profesor = self.request.user.username
        anio_activo = AnioEscolar.objects.filter(activo=True).first()

        if anio_activo:
            context['grupos'] = Horario.objects.filter(
                cedula_profesor=cedula_profesor,
                id_ano=anio_activo
            )
        else:
            context['grupos'] = []

        return context

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.get_form()
            form.data = request.POST
            form.files = request.FILES
            form.instance = self.get_object()

            if form.is_valid():
                actividad = form.save(commit=False)
                planificacion = actividad.id_pla
                fecha_actividad = actividad.fecha_Actividad

                # Validar fecha dentro del rango de la planificación
                if not (planificacion.fecha_inicio <= fecha_actividad <= planificacion.fecha_final):
                    mensaje = f"La fecha debe estar entre {planificacion.fecha_inicio} y {planificacion.fecha_final}."
                    error = {'fecha_Actividad': [mensaje]}
                    return JsonResponse({'mensaje': mensaje, 'error': error}, status=400)

                actividad.save()
                return JsonResponse({
                    'mensaje': 'La Actividad se ha editado correctamente',
                    'error': 'No hay error',
                    'redirect_url': reverse('consultargrupo'),
                }, status=200)
            else:
                return JsonResponse({'mensaje': 'Error al actualizar la actividad', 'error': form.errors}, status=400)
        else:
            return redirect('consultargrupo')

class RegistrarActividad(CreateView):
    model = Actividad
    form_class = ActividadForm
    template_name = 'Actividad/registrarActividad.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        cedula_profesor = self.request.user.username
        anio_activo = AnioEscolar.objects.filter(activo=True).first()

        if anio_activo:
            grupos_ids = Horario.objects.filter(
                cedula_profesor=cedula_profesor,
                id_ano=anio_activo
            ).values_list('id_g__pk', flat=True)
        else:
            grupos_ids = Intere.objects.none().values_list('pk', flat=True)

        form.fields['id_g'].queryset = Intere.objects.filter(pk__in=grupos_ids)
        form.fields['id_pla'].queryset = Planificacion.objects.filter(id_g__in=grupos_ids)

        return form

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = self.get_form()
            form.data = request.POST
            form.files = request.FILES

            if form.is_valid():
                actividad = form.save(commit=False)
                planificacion = actividad.id_pla
                fecha_actividad = actividad.fecha_Actividad

                if not (planificacion.fecha_inicio <= fecha_actividad <= planificacion.fecha_final):
                    mensaje = f"La fecha debe estar entre {planificacion.fecha_inicio} y {planificacion.fecha_final}."
                    error = {'fecha_Actividad': [mensaje]}
                    return JsonResponse({'mensaje': mensaje, 'error': error}, status=400)

                total_actividades = Actividad.objects.filter(id_pla=planificacion).count()
                if total_actividades >= planificacion.limite_actividades:
                    mensaje = f"Límite de {planificacion.limite_actividades} actividades alcanzado."
                    error = {'limite_actividades': [mensaje]}
                    return JsonResponse({'mensaje': mensaje, 'error': error}, status=400)

                actividad.save()
                return JsonResponse({
                    'mensaje': 'La Actividad se ha registrado correctamente',
                    'error': 'No hay error',
                    'redirect_url': reverse('consultargrupo'),
                }, status=201)
            else:
                return JsonResponse({'mensaje': 'La Actividad no se ha podido registrar', 'error': form.errors}, status=400)
        else:
            return redirect('consultargrupo')

class EliminarActividad(DeleteView):
    model = Actividad
    template_name = 'Actividad/eliminarActividad.html'
    success_url = reverse_lazy('inicio_Actividad')
    context_object_name = 'actividad'

    def delete(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            actividad = self.get_object()
            actividad.delete()
            mensaje = f'La Actividad se ha eliminado correctamente'
            error = 'No hay error'
            response = JsonResponse({'mensaje': mensaje, 'error': error})
            response.status_code = 201
            return response
        else:
            return redirect('ver_grupo_por_cedula')

class BuscarActividades(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        actividades = Actividad.objects.filter(nombre_actividad__icontains=query)
        results = [{'id': actividad.id_act, 'text': f'{actividad.nombre_actividad}{actividad.descripcion_actividad} - {actividad.fecha_Actividad}'} for actividad in actividades]
        return JsonResponse(results, safe=False)

#------------------------------ Notas ------------------------------#

def crear_anio_escolar(request):
    if request.method == 'POST':
        form = AnioEscolarForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_anios')  # Redirige a la lista de años escolares
    else:
        form = AnioEscolarForm()

    return render(request, 'anio_escolar/crear_anio.html', {'form': form})

def listar_anios(request):
    anios = AnioEscolar.objects.all().order_by('-fecha_inicio')
    return render(request, 'anio_escolar/listar_anios.html', {'anios': anios})

def activar_anio_escolar(request, pk):
    anio = get_object_or_404(AnioEscolar, pk=pk)
    # Desactivar todos
    AnioEscolar.objects.update(activo=False)
    # Activar el seleccionado
    anio.activo = True
    anio.save()
    return redirect('listar_anios')
