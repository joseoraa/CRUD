from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.urls import path

from .views import (Home, Login, logoutUsuario,CustomPasswordChangeView, RegistrarUsuario,unlock_user, 
                    ListarUsuario,EditarUsuario, EliminarUsuario, CambiarContraseñaModal, ListarEstudiante, EditarEstudiante, RegistrarEstudiante, EliminarEstudiante, 
                    BuscarEstudiantes,RegistrarProfesor, ListarProfesor, EditarProfesor, EliminarProfesor, BuscarProfesores,RegistrarCargo,ListarCargo,EditarCargo,
                    BuscarCargos,EliminarCargo,RegistrarIntere,ListarIntere,EliminarIntere,BuscarInteres,EditarIntere,RegistrarHorario,ListarHorario,EliminarHorario,
                    BuscarHorarios,EditarHorario,RegistrarInscripcion,ListarInscripcion,EditarInscripcion,EliminarInscripcion,BuscarInscripciones,exportar_notas_pdff)

from .views import (RegistrarPlanificacion,gestionar_fechas_corte,
                    exportar_notas_pdf,ver_estudiantes_por_grupo_notas,generar_reporte_pdf,ver_grupo_por_cedula,ListarPlanificacion,EditarPlanificacion,listar_grupos_ordenados,
                    EliminarPlanificacion,BuscarPlanificaciones,RegistrarActividad,ListarActividad,EditarActividad,EliminarActividad,BuscarActividades,listar_planificaciones,
                    ver_estudiantes_por_grupo,crear_anio_escolar,cambiar_estado_actividad,activar_anio_escolar,listar_anios,exportar_estudiantes_general_pdf,exportar_profesores_grupo_pdf,exportar_grupos_disponibles_pdf,exportar_asistencias_pdf)

from django.urls import reverse

from . import views

# ,EditarNota,RegistrarNota,EliminarNota,ListarNota,
# CambiarContraseña



urlpatterns = [

    #------------------------------ Inicio ------------------------------#

    path('', login_required(Home.as_view()), name="home"),
    path('accounts/login/', Login.as_view(), name="login"),
    path('logout/', login_required(logoutUsuario), name='logout'),
    path('unlock_user/<int:user_id>/',login_required (unlock_user), name='unlock_user'),

    #------------------------------ Usuario ------------------------------#

    path('registrarUsuario/', login_required(RegistrarUsuario.as_view()), name="registrar_Usuario"),
    path('inicioUsuario/', login_required(
                                TemplateView.as_view(
                                    template_name = 'Usuario/listarUsuario.html'
                                    )
                                ), name="inicio_Usuario"),
    path('listarUsuario/', login_required(ListarUsuario.as_view()), name="listar_Usuario"),
    path('editarUsuario/<int:pk>/', login_required(EditarUsuario.as_view()), name="editar_Usuario"),
    path('eliminarUsuario/<int:pk>/', login_required(EliminarUsuario.as_view()), name="eliminar_Usuario"),
    
    
    path('cambiocontraseña/',login_required(  CustomPasswordChangeView.as_view()), name='cambiocontraseña'),
    path('cambiarContraseña/<int:pk>/', login_required(CambiarContraseñaModal.as_view()), name="cambiar_Contraseña"),
    

   #------------------------------ Estudiante ------------------------------#
    path('registrarEstudiante/', login_required(RegistrarEstudiante.as_view()), name="registrar_Estudiante"),
    path('inicioEstudiante/', login_required(
                                TemplateView.as_view(
                                    template_name='Estudiante/listarEstudiante.html'
                                    )
                                ), name="inicio_Estudiante"),
    path('listarEstudiante/', login_required(ListarEstudiante.as_view()), name="listar_Estudiante"),
    path('editarEstudiante/<int:pk>/', login_required(EditarEstudiante.as_view()), name="editar_Estudiante"),
    path('eliminarEstudiante/<int:pk>/', login_required(EliminarEstudiante.as_view()), name="eliminar_Estudiante"),
    path('buscarEstudiante/', login_required(BuscarEstudiantes.as_view()), name='buscar_Estudiante'),
    
    # path('consultarestudiante/', login_required(ver_estudiantes_por_grupo), name="consultarestudiante"),   

    path('consultar-estudiantes/', ver_estudiantes_por_grupo, name='consultar_estudiantes'),
    path('generar-reporte-pdf/', generar_reporte_pdf, name='generar_reporte_pdf'),
    path('consultar-estudiantes-notas/', ver_estudiantes_por_grupo_notas, name='consultar_estudiantes_notas'),
    path('exportar-notas-pdf/', exportar_notas_pdf, name='exportar_notas_pdf'),
    path('exportar-grupos-disponibles/', exportar_grupos_disponibles_pdf, name='exportar_grupos_disponibles_pdf'),


   # urls.py
    path('exportar_notas_pdff/<str:lapso>/', exportar_notas_pdff, name='exportar_notas_pdff'),



    # path('fechas-corte/', gestionar_fechas_corte, name='gestionar_fechas_corte'),
    path('fechas-corte/', gestionar_fechas_corte, name='gestionar_fechas_corte'),
    path('exportar-asistencias-pdf/',exportar_asistencias_pdf, name='exportar_asistencias_pdf'),


   #------------------------------ PDF  ------------------------------#
   #------------------------------ PDF  ------------------------------#
   #------------------------------ PDF  ------------------------------#
   #------------------------------ PDF  ------------------------------#
   #------------------------------ PDF  ------------------------------#
   #------------------------------ PDF  ------------------------------#
   #------------------------------ PDF  ------------------------------#
   #------------------------------ PDF  ------------------------------#

    path('exportar-estudiantes-pdf/', exportar_estudiantes_general_pdf, name='exportar_estudiantes_pdf'),

    path('exportar_estudiantes_masculinos_pdf/', views.exportar_estudiantes_masculinos_pdf, name='exportar_estudiantes_masculinos_pdf'),
    path('exportar_estudiantes_femeninas_pdf/', views.exportar_estudiantes_femeninas_pdf, name='exportar_estudiantes_femeninas_pdf'),
    
    path('exportar-profesores-pdf/', exportar_profesores_grupo_pdf, name='exportar_profesores_pdf'),



   #------------------------------ cargo  ------------------------------#
    path('registrarCargo/', login_required(RegistrarCargo.as_view()), name="registrar_Cargo"),
    path('inicioCargo/', login_required(
                                TemplateView.as_view(
                                    template_name = 'Cargo/listarCargo.html'
                                    )
                                ), name="inicio_Cargo"),
    path('listarCargo/', login_required(ListarCargo.as_view()), name="listar_Cargo"),
    path('editarCargo/<int:pk>/', login_required(EditarCargo.as_view()), name="editar_Cargo"),
    path('eliminarCargo/<int:pk>/', login_required(EliminarCargo.as_view()), name="eliminar_Cargo"),
    path('buscarCargos/', login_required(BuscarCargos.as_view()), name='buscar_Cargos'),



   #------------------------------ Profesor ------------------------------#

    path('registrarProfesor/', login_required(RegistrarProfesor.as_view()), name="registrar_Profesor"),
    path('inicioProfesor/', login_required(
                                TemplateView.as_view(
                                    template_name = 'Profesor/listarProfesor.html'
                                    )
                                ), name="inicio_Profesor"),
    path('listarProfesor/', login_required(ListarProfesor.as_view()), name="listar_Profesor"),
    path('editarProfesor/<int:pk>/', login_required(EditarProfesor.as_view()), name="editar_Profesor"),
    path('eliminarProfesor/<int:pk>/', login_required(EliminarProfesor.as_view()), name="eliminar_Profesor"),
    path('buscarProfesor/', login_required(BuscarProfesores.as_view()), name='buscar_Profesor'),

   #------------------------------ Grupo  ------------------------------#
    path('registrarIntere/', login_required(RegistrarIntere.as_view()), name="registrar_Intere"),
    path('inicioIntere/', login_required(
                                TemplateView.as_view(
                                    template_name = 'Intere/listarIntere.html'
                                    )
                                ), name="inicio_Intere"),
    path('listarIntere/', login_required(ListarIntere.as_view()), name="listar_Intere"),
    path('editarIntere/<int:pk>/', login_required(EditarIntere.as_view()), name="editar_Intere"),
    path('eliminarIntere/<int:pk>/', login_required(EliminarIntere.as_view()), name="eliminar_Intere"),
    path('buscarIntere/', login_required(BuscarInteres.as_view()), name='buscar_Intere'),

    path('listado/', views.listar_grupos_ordenados, name='listado_grupos'),

    path('listadohorario/', views.horarios_por_turno, name='listado_estudiante_horario'),


   #------------------------------ Horario ------------------------------#

    path('registrarHorario/', login_required(RegistrarHorario.as_view()), name="registrar_Horario"),
    path('inicioHorario/', login_required(
                                TemplateView.as_view(
                                    template_name = 'Horario/listarHorario.html'
                                    )
                                ), name="inicio_Horario"),
    path('listarHorario/', login_required(ListarHorario.as_view()), name="listar_Horario"),
    path('editarHorario/<int:pk>/', login_required(EditarHorario.as_view()), name="editar_Horario"),
    path('eliminarHorario/<int:pk>/', login_required(EliminarHorario.as_view()), name="eliminar_Horario"),
    path('buscarHorario/', login_required(BuscarHorarios.as_view()), name='buscar_Horario'),

    #------------------------------ Inscripcion ------------------------------#
    path('registrarInscripcion/', login_required(RegistrarInscripcion.as_view()), name="registrar_Inscripcion"),
    path('inicioInscripcion/', login_required(
                                TemplateView.as_view(
                                    template_name = 'Inscripcion/listarInscripcion.html'
                                    )
                                ), name="inicio_Inscripcion"),
    path('listarInscripcion/', login_required(ListarInscripcion.as_view()), name="listar_Inscripcion"),
    path('editarInscripcion/<int:pk>/', login_required(EditarInscripcion.as_view()), name="editar_Inscripcion"),
    path('eliminarInscripcion/<int:pk>/', login_required(EliminarInscripcion.as_view()), name="eliminar_Inscripcion"),
    path('buscarInscripcion/', login_required(BuscarInscripciones.as_view()), name='buscar_Inscripcion'),

    #------------------------------ planificacion ------------------------------#
    path('registrarPlanificacion/', login_required(RegistrarPlanificacion.as_view()), name="registrar_Planificacion"),
    path('consultargrupo/', login_required(ver_grupo_por_cedula), name="consultargrupo"),
    path('grupo/por-cedula/', views.ver_grupo_por_cedula, name='ver_grupo_por_cedula'),
    path('planificaciones/', listar_planificaciones, name='listar_planificaciones'),
    path('planificaciones/<int:actividad_id>/cambiar_estado/', cambiar_estado_actividad, name='cambiar_estado_actividad'),







    path('registrarPlanificacion/', login_required(RegistrarPlanificacion.as_view()), name="registrar_Planificacion"),
    path('inicioPlanificacion/', login_required(
                                TemplateView.as_view(
                                    template_name = 'Planificacion/listarPlanificacion.html'
                                    )
                                ), name="inicio_Planificacion"),
    path('listarPlanificacion/', login_required(ListarPlanificacion.as_view()), name="listar_Planificacion"),
    path('editarPlanificacion/<int:pk>/', login_required(EditarPlanificacion.as_view()), name="editar_Planificacion"),
    path('eliminarPlanificacion/<int:pk>/', login_required(EliminarPlanificacion.as_view()), name="eliminar_Planificacion"),
    path('buscarPlanificaciones/', login_required(BuscarPlanificaciones.as_view()), name='buscar_Planificacion'),

    #----------------------------- Actividad ------------------------------#
    

    path('inicioActividad/', login_required(
                                TemplateView.as_view(
                                    template_name = 'Actividad/listarActividad.html'
                                    )
                                ), name="inicio_Actividad"),
    path('listarActividad/', login_required(ListarActividad.as_view()), name="listar_Actividad"),
    path('editarActividad/<int:pk>/', login_required(EditarActividad.as_view()), name="editar_Actividad"),
    path('registrarActividad/', login_required(RegistrarActividad.as_view()), name="registrar_Actividad"),
    path('eliminarActividad/<int:pk>/', login_required(EliminarActividad.as_view()), name="eliminar_Actividad"),
    path('buscarActividades/', login_required(BuscarActividades.as_view()), name='buscar_Actividad'),
    
    #----------------------------- NOTA ------------------------------#
    path('asistencias/', views.ver_estudiantes_por_grupo_asistencia, name='consultar_estudiantes_asistencia'),

    
    # path('reporte/estudiantes/', login_required('generar_pdf_estudiantes'), name='reporte_estudiantes'),
    path('anio-escolar/nuevo/', login_required(crear_anio_escolar), name='crear_anio'),
    
    path('anios/activar/<int:pk>/', login_required(activar_anio_escolar), name='activar_anio_escolar'),
    path('anios/',login_required(listar_anios), name='listar_anios'),






]

    
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)