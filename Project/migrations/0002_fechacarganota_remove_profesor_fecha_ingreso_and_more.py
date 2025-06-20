# Generated by Django 5.0.1 on 2025-06-09 18:30

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Project', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FechaCargaNota',
            fields=[
                ('id_carganota', models.AutoField(primary_key=True, serialize=False, verbose_name='ID de Carga de Notas')),
                ('corte_1_inicio', models.DateField(blank=True, null=True)),
                ('corte_1_fin', models.DateField(blank=True, null=True)),
                ('corte_2_inicio', models.DateField(blank=True, null=True)),
                ('corte_2_fin', models.DateField(blank=True, null=True)),
                ('corte_3_inicio', models.DateField(blank=True, null=True)),
                ('corte_3_fin', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='profesor',
            name='fecha_ingreso',
        ),
        migrations.AddField(
            model_name='actividad',
            name='evaluada',
            field=models.BooleanField(default=False, verbose_name='¿Actividad Evaluada?'),
        ),
        migrations.AddField(
            model_name='actividad',
            name='fecha_evaluacion',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha de evaluación'),
        ),
        migrations.AddField(
            model_name='anioescolar',
            name='activo',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='estudiante',
            name='Sexo',
            field=models.CharField(default=1, max_length=50, verbose_name='Sexo *'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='asistencia',
            name='id_estudiante',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Project.inscripcion', verbose_name='Inscripción'),
        ),
        migrations.AlterField(
            model_name='asistencia',
            name='id_g',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Project.intere', verbose_name='Grupo'),
        ),
        migrations.AlterField(
            model_name='inscripcion',
            name='id_estudiante',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Project.estudiante', verbose_name='Estudiante'),
        ),
        migrations.AlterField(
            model_name='nota',
            name='corte_1',
            field=models.DecimalField(blank=True, decimal_places=0, max_digits=2, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(20)]),
        ),
        migrations.AlterField(
            model_name='nota',
            name='corte_2',
            field=models.DecimalField(blank=True, decimal_places=0, max_digits=2, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(20)]),
        ),
        migrations.AlterField(
            model_name='nota',
            name='corte_3',
            field=models.DecimalField(blank=True, decimal_places=0, max_digits=2, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(20)]),
        ),
        migrations.AlterUniqueTogether(
            name='asistencia',
            unique_together={('id_estudiante', 'id_g', 'encuentro_numero')},
        ),
    ]
