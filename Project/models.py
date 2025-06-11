from django.db import models
import time
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator, MinLengthValidator, RegexValidator
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError
import datetime
from django.utils.timezone import now
# Create your models here.


#------------------------------ Usuario ------------------------------#

class UsuarioManager(BaseUserManager):
    def create_user(self, email, username, nombre, apellido, password = None):
        if not email:
            raise ValueError('El usuario debe tener un correo electrónico')

        usuario = self.model(
            username = username,
            nombre = nombre,
            apellido = apellido,
            email = self.normalize_email(email)
        )

        usuario.set_password(password)
        usuario.save()
        return usuario

    def create_superuser(self, username, nombre, apellido, email, password):
        usuario = self.create_user(
            email,
            username = username,
            nombre = nombre,
            apellido = apellido,
            password = password
        )
        usuario.usuario_administrador = True
        usuario.save()
        return usuario

class Usuario(AbstractBaseUser):
    cod_usuario = models.AutoField(
        'Codigo', primary_key=True, blank=False, null=False)
    username = models.CharField(
        'Cedula', unique=True, max_length=100)
    nombre = models.CharField(
        'Nombre', max_length=30, validators=[MinLengthValidator(2)], blank=False, null=False)
    apellido = models.CharField(
        'Apellido', max_length=30, validators=[MinLengthValidator(2)], blank=False, null=False)
    email = models.EmailField(
        'Correo electrónico ', unique=True, max_length=100, blank=False, null=False)
    usuario_administrador = models.BooleanField(
        default=False)
    objects = UsuarioManager()
    intentos_fallidos = models.PositiveIntegerField(default=0)
    cuenta_bloqueada = models.BooleanField(default=False)


    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['nombre', 'apellido', 'email']

    def __str__(self):
        return f'{self.username}'

    def has_perm(self, perm, obj = None):
        return True

    def has_module_perms(self, app_label):
        return True

    def save(self, *args, **kwargs):
        self.username = (self.username).upper()
        self.nombre = (self.nombre).upper()
        self.apellido = (self.apellido).upper()
        self.email = (self.email).upper()
        return super(Usuario, self).save(*args, **kwargs)

    @property
    def is_staff(self):
        return self.usuario_administrador


#------------------------------ Estudiantes ------------------------------#

class Estudiante(models.Model):
    id_estudiante = models.AutoField(
        'Codigo del Estudiante', primary_key=True, blank=False, null=False)
    tipo_cedula_estudiante = models.CharField(
        max_length=2, blank=False, null=False)
    cedula_estudiante = models.CharField(
        'Cédula *', unique=True, max_length=8, validators=[MinLengthValidator(7)], blank=False, null=False)
    nombre_estudiante= models.CharField(
        'Nombres *', max_length=30, validators=[MinLengthValidator(2)], blank=False, null=False)
    apellido_estudiante = models.CharField(
        'Apellidos * ', max_length=30, validators=[MinLengthValidator(2)], blank=False, null=False)
    Sexo = models.CharField(
        'Sexo *',max_length=50, blank=False, null=False)
    telefono_estudiante = models.CharField(
        'Teléfono', 
        max_length=11, 
        blank=True,  # Permite que el campo esté vacío en formularios
        null=True    # Permite que el campo sea nulo en la base de datos
    )
    correo_estudiante = models.EmailField( 'Correo',
        blank=True,  # Permite que el campo esté vacío en formularios
        null=True    # Permite que el campo sea nulo en la base de datos
    )
    
    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        ordering = ['cedula_estudiante']

    def __str__(self):
        return f'{self.tipo_cedula_estudiante}{self.cedula_estudiante} - {self.nombre_estudiante} {self.apellido_estudiante}'

    def save(self, *args, **kwargs):
        self.nombre_estudiante = (self.nombre_estudiante).upper()
        self.apellido_estudiante = (self.apellido_estudiante).upper()
    # Verifica si el correo tiene un valor antes de convertirlo a mayúsculas
        if self.correo_estudiante:
            self.correo_estudiante = self.correo_estudiante.upper()
            
        if self.telefono_estudiante:
            self.telefono_estudiante = self.telefono_estudiante
        else:
            self.telefono_estudiante = ""
            self.correo_estudiante= ""
                    
        return super(Estudiante, self).save(*args, **kwargs)
    
    
       #------------------------------ Cargo ------------------------------#
 
class Cargo(models.Model):
    id_cargo = models.AutoField(
        'Codigo del Cargo', primary_key=True, blank=False, null=False)
    nombre_cargo = models.CharField(
        'Especialidad *',unique=True,   max_length=50, blank=False, null=False)

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['nombre_cargo']

    def __str__(self):
        return f'{self.nombre_cargo}'

    def save(self, *args, **kwargs):
        self.nombre_cargo = (self.nombre_cargo).upper()
        return super(Cargo, self).save(*args, **kwargs)  
    


    #------------------------------ Profesor ------------------------------#
    
class Profesor(models.Model):
    id_p = models.AutoField('Codigo de Profesor', primary_key=True, blank=False,null=False)
    tipo_cedula_profesor = models.CharField(
        max_length=2, blank=False, null=False)
    cedula_profesor = models.CharField(
        'Cedula del Profesor *', unique=True, max_length=8, validators=[MinLengthValidator(7)], blank=False, null=False)
    nombre_profesor= models.CharField(
        'Nombre del Profesor *', max_length=30, validators=[MinLengthValidator(2)], blank=False, null=False)
    apellido_profesor = models.CharField(
        'Apellido del Profesor * ', max_length=30, validators=[MinLengthValidator(2)], blank=False, null=False)
    telefono_Profesor = models.CharField(
        'Telefono del Profesor ', max_length=11, validators=[MinLengthValidator(11)], blank=True, null=True)
    id_cargo = models.ForeignKey(
        Cargo, verbose_name='Cargo *', on_delete=models.PROTECT)
    nombre_cargo = models.TextField(
        'Cargo del Trabajador *', blank=False, null=False)
    
    class Meta:
        verbose_name = 'Profesor'
        verbose_name_plural = 'Profesores'
        ordering = ['cedula_profesor']

    def __str__(self):
        return f'{self.tipo_cedula_profesor}{self.cedula_profesor} - {self.nombre_profesor} {self.apellido_profesor} - {self.nombre_cargo}'

    def save(self, *args, **kwargs):
        self.nombre_profesor = (self.nombre_profesor).upper()
        self.apellido_profesor = (self.apellido_profesor).upper()
        self.nombre_cargo = self.id_cargo.nombre_cargo

        if self.telefono_Profesor:
            self.telefono_Profesor=self.telefono_Profesor
        else:
            self.telefono_Profesor= ""

        return super(Profesor, self).save(*args, **kwargs)
    #------------------------------ Grupo ------------------------------#

class Intere (models.Model):
    id_g = models.AutoField(
        'Codigo del Grupo ', primary_key=True, blank=False,null=False)
    nombre_grupo = models.CharField(
        'Nombre del Grupo *',unique=True, max_length=30, validators=[MinLengthValidator(2)], blank=False, null=False)
    descripcion_grupo = models.CharField('Descripcion del Grupo', max_length=40, blank=True,null=True)
    contador_estudiantes = models.IntegerField(
        'Cantidad de Estudiantes', blank=True, null=True)
    status = models.CharField('Estado', max_length=15, blank=False,null=False)

    class Meta:
        verbose_name = 'Intere'
        verbose_name_plural = 'Interes'
        ordering = ['nombre_grupo']
        
    def __str__(self):
        return f'{self.nombre_grupo} - {self.status}'
    
    
    def save(self, *args, **kwargs):
        self.nombre_grupo= (self.nombre_grupo).upper()
        self.status
        if self.descripcion_grupo:
            self.descripcion_grupo = self.descripcion_grupo.upper()
        else:
            self.descripcion_grupo = ""        

        return super(Intere, self).save(*args, **kwargs)
 
 
 
class AnioEscolar(models.Model):
    id_ano = models.AutoField('ID del año', primary_key=True, blank=False, null=False)
    nombreano = models.CharField(' Nombre*', max_length=9, blank=False, null=False)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Año Escolar"
        verbose_name_plural = "Años Escolares"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f'{self.nombreano}'

    def save(self, *args, **kwargs):
        # Generar el nombre del año basado en las fechas
        if self.fecha_inicio and self.fecha_fin:
            self.nombreano = f"{self.fecha_inicio.year}-{self.fecha_fin.year}"

        # Si este año se marca como activo, desactivar los otros
        if self.activo:
            AnioEscolar.objects.exclude(pk=self.pk).update(activo=False)

        super().save(*args, **kwargs)
 

#------------------------------ horario ------------------------------#

class Horario(models.Model):
    id_h=models.AutoField(
        'Codigo del Horario', primary_key=True, blank=False, null=False)
    semana_grupo = models.CharField(
        max_length=12, blank=False, null=False)
    hora_inicio = models.TimeField()
    hora_final = models.TimeField()
    
    id_g=models.ForeignKey(Intere, verbose_name='Grupo de Interes * ',on_delete=models.PROTECT,blank=False,null=False)
    nombre_grupo = models.TextField('Nombre',blank=False,null=False)
    
    id_p= models.ForeignKey(Profesor, verbose_name='Profesor Asignado * ',on_delete=models.PROTECT,blank=False,null=False)
    tipo_cedula_profesor = models.CharField (max_length=2, blank=False, null=False)
    cedula_profesor = models.TextField(
        'Cedula del Profesor',blank=False, null=False)
    nombre_profesor= models.TextField(
        'Nombre del Profesor',blank=False, null=False)
    apellido_profesor = models.TextField(
        'Apellido del Profesor',blank=False, null=False)
    
        # Relación con Año Escolar
    id_ano = models.ForeignKey(
        AnioEscolar,
        verbose_name='Año Escolar',
        on_delete=models.PROTECT,
        blank=False,
        null=False)

    nombreano = models.TextField('Nombre',blank=False,null=False)
    
    class Meta:
        verbose_name= 'Horario'
        verbose_name_plural = 'Horarios'
        ordering = ['semana_grupo']
                 
        
    def __str__(self):
        return f'{self.nombre_grupo}  {self.hora_inicio}-{self.hora_final}'
      
      
    def save(self, *args, **kwargs):
        self.semana_grupo = self.semana_grupo.upper()
        if self.id_g:
            
            self.nombre_grupo = self.id_g.nombre_grupo
            
        if self.id_ano:
            self.nombreano = self.id_ano.nombreano


        
        if self.id_p:
            self.tipo_cedula_profesor = self.id_p.tipo_cedula_profesor
            self.cedula_profesor = self.id_p.cedula_profesor
            self.nombre_profesor = self.id_p.nombre_profesor
            self.apellido_profesor = self.id_p.apellido_profesor
            

        self.full_clean()
        return super(Horario, self).save(*args, **kwargs)
    

# BASE DE DATOS DE INSCRIPCIONES    
    
class Inscripcion(models.Model):
    id_inscripcion = models.AutoField('ID de Inscripción', primary_key=True)
    
    seccion = models.CharField(
        max_length=20, blank=False, null=False)
    ano_curso = models.CharField(
        'Año Cursante *', max_length=4, validators=[MinLengthValidator(1)], blank=False, null=False)
    
    id_estudiante = models.ForeignKey(Estudiante, verbose_name='Estudiante', on_delete=models.PROTECT)
    tipo_cedula_estudiante = models.CharField(max_length=2)
    cedula_estudiante = models.CharField('Cédula del Estudiante *', max_length=20)
    nombre_estudiante = models.CharField('Nombres del Estudiante *', max_length=100)
    apellido_estudiante = models.CharField('Apellidos del Estudiante *', max_length=100)
    
    id_g = models.ForeignKey(Intere, verbose_name='grupo', on_delete=models.PROTECT,)
    nombre_grupo = models.CharField('Nombre', max_length=100)

    id_ano = models.ForeignKey(
        AnioEscolar,
        verbose_name='Año Escolar',
        on_delete=models.PROTECT,
        blank=False,
        null=False)

    nombreano = models.TextField('Nombre',blank=False,null=False)
   
    def __str__(self):
            return f'{self.tipo_cedula_estudiante}{self.cedula_estudiante}- {self.nombre_estudiante} {self.apellido_estudiante} - {self.nombreano}-{self.seccion}'
    

    def save(self, *args, **kwargs):
        
        if self.id_ano:
            self.nombreano = self.id_ano.nombreano
            
        self.nombre_grupo = self.id_g.nombre_grupo
        # Actualizar los datos del estudiante
        self.tipo_cedula_estudiante = self.id_estudiante.tipo_cedula_estudiante
        self.cedula_estudiante = self.id_estudiante.cedula_estudiante
        self.nombre_estudiante = self.id_estudiante.nombre_estudiante
        self.apellido_estudiante = self.id_estudiante.apellido_estudiante

        # Incrementar el contador de inscripciones en el grupo asociado
        self.clean()
        return super(Inscripcion, self).save(*args, **kwargs)
    
    

    #------------------------------ planificacion ------------------------------#

class Planificacion(models.Model):
    id_pla= models.AutoField('ID de Planificacion', primary_key=True)
    nombre_pla = models.CharField('Nombre de la Planificacion *', max_length=40, validators=[MinLengthValidator(2)], blank=False, null=False)
    fecha_inicio = models.DateField('Por Favor Ingrese Fecha de Inicio de la planificacion *', blank=False, null=False)
    fecha_final = models.DateField('Por Favor Ingrese Fecha de Final de la planificacion *', blank=False, null=False)
    observacion = models.CharField('Observacion de la planificación', max_length=40, blank=True, null=True)
    
    id_g = models.ForeignKey(Intere, verbose_name='Grupo', on_delete=models.PROTECT, blank=False, null=False)
    nombre_grupo = models.TextField('Nombre', blank=False, null=False)


    limite_actividades = models.PositiveIntegerField('Límite de Actividades', default=1, blank=False, null=False)

    
    
    def __str__(self):
        return f'{self.nombre_pla}'
    
    def save (self, *args, **kwargs):
        self.nombre_grupo=self.id_g.nombre_grupo
        self.nombre_pla=(self.nombre_pla).upper()
   # Convert observacion to uppercase if it has any letters
        if self.observacion:
            self.observacion = self.observacion.upper()
        else:
            self.observacion = "" 
                
        # Incrementar el contador de Actividad en el grupo asociado
        self.clean()
        return super(Planificacion, self).save(*args, **kwargs)
    
    
    #----------------------------actividad ------------------------------#

class Actividad(models.Model):
    id_act = models.AutoField('ID de Actividad', primary_key=True)

    nombre_actividad = models.CharField(
        'Nombre del Actividad *', max_length=30, validators=[MinLengthValidator(2)], blank=False, null=False
    )
    descripcion_actividad = models.CharField('Descripcion de la Actividad', max_length=40, blank=True, null=True)
    fecha_Actividad = models.DateField('Por Favor Ingrese Fecha de la Actividad', blank=False, null=False)
    evaluada = models.BooleanField('¿Actividad Evaluada?', default=False)
    fecha_evaluacion = models.DateField('Fecha de evaluación', blank=True, null=True)

    id_pla = models.ForeignKey(Planificacion, verbose_name='Planificación', on_delete=models.PROTECT)
    nombre_pla = models.CharField('Nombre', max_length=100)

    id_g = models.ForeignKey(Intere, verbose_name='Grupo', on_delete=models.PROTECT, blank=False, null=False)
    nombre_grupo = models.TextField('Nombre', blank=False, null=False)

    
    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering = ['fecha_Actividad']
        
    def evaluada_display(self):
            return "Sí" if self.evaluada else "No"

    def __str__(self):
        evaluada_str = "Sí" if self.evaluada else "No"
        return f'{self.nombre_actividad} ({self.fecha_Actividad}) - Evaluada: {evaluada_str}'


    def save(self, *args, **kwargs):
        self.nombre_grupo=self.id_g.nombre_grupo
        self.nombre_pla=self.id_pla.nombre_pla
        self.nombre_actividad = (self.nombre_actividad).upper()
        
        if self.descripcion_actividad:
            self.descripcion_actividad = self.descripcion_actividad.upper()
        else:
            self.descripcion_actividad = "" 

        # Si se marca como evaluada y no tiene fecha, la asigna
        if self.evaluada and not self.fecha_evaluacion:
            self.fecha_evaluacion = now().date()
        elif not self.evaluada:
            self.fecha_evaluacion = None


        self.full_clean()  # Ejecuta el clean() antes de guardar
        return super(Actividad, self).save(*args, **kwargs)   

#----------------------------NOTAS  ------------------------------#class

class Nota(models.Model):
    id_inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE, verbose_name='Inscripción')

    corte_1 = models.DecimalField(
        max_digits=2, decimal_places=0, 
        validators=[MinValueValidator(0), MaxValueValidator(20)],  # 🔥 validaciones de 1 a 20
        null=True, blank=True
    )
    corte_2 = models.DecimalField(
        max_digits=2, decimal_places=0, 
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        null=True, blank=True
    )
    corte_3 = models.DecimalField(
        max_digits=2, decimal_places=0, 
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        null=True, blank=True
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)  # fecha cuando se crea
    fecha_actualizacion = models.DateTimeField(null=True, blank=True)  # ⏰ nueva fecha para cuando se edita



    def __str__(self):
        return f"Notas de {self.id_inscripcion.nombre_estudiante} para el grupo {self.id_inscripcion.nombre_grupo}"



#----------------------------Asistencia  ------------------------------#

class Asistencia(models.Model):
    id_estudiante = models.ForeignKey(Inscripcion, on_delete=models.CASCADE, verbose_name='Inscripción')  # Inscripción del estudiante
    id_g = models.ForeignKey(Intere, verbose_name='Grupo', on_delete=models.PROTECT)

    encuentro_numero = models.IntegerField()  # Número del encuentro (1 al 10)

    asistio = models.BooleanField(default=False)
    fecha_encuentro = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('id_estudiante', 'id_g', 'encuentro_numero')

    def __str__(self):
        return f"{self.id_estudiante.nombre_estudiante} - Encuentro {self.encuentro_numero} - {'Asistió' if self.asistio else 'No asistió'}"


#----------------------------prueba  ------------------------------#
#----------------------------prueba  ------------------------------#

class FechaCargaNota(models.Model):
    id_carganota = models.AutoField('ID de Carga de Notas', primary_key=True)
   
    corte_1_inicio = models.DateField(null=True, blank=True)
    corte_1_fin = models.DateField(null=True, blank=True)

    corte_2_inicio = models.DateField(null=True, blank=True)
    corte_2_fin = models.DateField(null=True, blank=True)

    corte_3_inicio = models.DateField(null=True, blank=True)
    corte_3_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Fechas para las cargas de Notas"


