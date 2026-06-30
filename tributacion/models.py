from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import F
from decimal import Decimal

class Mercado(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'mercado'
        verbose_name = 'Mercado'
        verbose_name_plural = 'Mercados'

    def __str__(self):
        return self.nombre


class Instrumento(models.Model):
    nemotecnico = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    mercado = models.ForeignKey(Mercado, on_delete=models.PROTECT, related_name='instrumentos')
    inscrito = models.BooleanField(default=True)

    class Meta:
        db_table = 'instrumento'
        verbose_name = 'Instrumento'
        verbose_name_plural = 'Instrumentos'

    def __str__(self):
        return f"{self.nemotecnico} ({self.mercado.nombre})"


class CalificacionTributaria(models.Model):
    ejercicio = models.IntegerField()
    mercado = models.ForeignKey(Mercado, on_delete=models.PROTECT)
    instrumento = models.ForeignKey(Instrumento, on_delete=models.PROTECT)
    fecha_pago = models.DateField()
    secuencia = models.IntegerField()
    nro_dividendo = models.IntegerField()
    tipo_sociedad = models.CharField(max_length=1)  # 'A' o 'C'
    valor_historico = models.DecimalField(max_digits=18, decimal_places=4)
    fuente_ingreso = models.CharField(max_length=50)  # 'Manual', 'Carga Masiva Factores', etc.
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    isfut = models.BooleanField(default=False)
    factor_actualizacion = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0.00000000'))
    corredor_propietario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='calificaciones')

    # Factores del 8 al 37 (precisión de 9 dígitos y 8 decimales)
    factor_8 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_9 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_10 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_11 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_12 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_13 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_14 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_15 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_16 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_17 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_18 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_19 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_20 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_21 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_22 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_23 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_24 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_25 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_26 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_27 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_28 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_29 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_30 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_31 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_32 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_33 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_34 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_35 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_36 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))
    factor_37 = models.DecimalField(max_digits=9, decimal_places=8, default=Decimal('0.00000000'))

    # Montos opcionales del 8 al 19 (para el cálculo de factores)
    monto_8 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto_9 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto_10 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto_11 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto_12 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto_13 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto_14 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto_15 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto_16 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto_17 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto_18 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    monto_19 = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'calificacion_tributaria'
        unique_together = ('ejercicio', 'instrumento', 'secuencia', 'corredor_propietario')
        verbose_name = 'Calificación Tributaria'
        verbose_name_plural = 'Calificaciones Tributarias'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(secuencia__gt=10000),
                name='chk_secuencia_minima'
            ),
            models.CheckConstraint(
                condition=models.Q(tipo_sociedad__in=['A', 'C']),
                name='chk_tipo_sociedad'
            ),
            models.CheckConstraint(
                condition=models.Q(
                    factor_8__lte=Decimal('1.00000000') - F('factor_9') - F('factor_10') - F('factor_11') -
                                  F('factor_12') - F('factor_13') - F('factor_14') - F('factor_15') -
                                  F('factor_16') - F('factor_17') - F('factor_18') - F('factor_19')
                ),
                name='chk_suma_factores'
            )
        ]

    def clean(self):
        # Calcular factores si se ingresaron montos
        montos = [
            self.monto_8, self.monto_9, self.monto_10, self.monto_11,
            self.monto_12, self.monto_13, self.monto_14, self.monto_15,
            self.monto_16, self.monto_17, self.monto_18, self.monto_19
        ]
        
        # Validar si al menos un monto no es nulo y es mayor a cero
        if any(m is not None for m in montos):
            suma_montos = sum(Decimal(str(m or 0)) for m in montos)
            if suma_montos > 0:
                self.factor_8 = round(Decimal(str(self.monto_8 or 0)) / suma_montos, 8)
                self.factor_9 = round(Decimal(str(self.monto_9 or 0)) / suma_montos, 8)
                self.factor_10 = round(Decimal(str(self.monto_10 or 0)) / suma_montos, 8)
                self.factor_11 = round(Decimal(str(self.monto_11 or 0)) / suma_montos, 8)
                self.factor_12 = round(Decimal(str(self.monto_12 or 0)) / suma_montos, 8)
                self.factor_13 = round(Decimal(str(self.monto_13 or 0)) / suma_montos, 8)
                self.factor_14 = round(Decimal(str(self.monto_14 or 0)) / suma_montos, 8)
                self.factor_15 = round(Decimal(str(self.monto_15 or 0)) / suma_montos, 8)
                self.factor_16 = round(Decimal(str(self.monto_16 or 0)) / suma_montos, 8)
                self.factor_17 = round(Decimal(str(self.monto_17 or 0)) / suma_montos, 8)
                self.factor_18 = round(Decimal(str(self.monto_18 or 0)) / suma_montos, 8)
                self.factor_19 = round(Decimal(str(self.monto_19 or 0)) / suma_montos, 8)

        # Validación backend de la suma de factores del 8 al 19
        suma_factores = (
            self.factor_8 + self.factor_9 + self.factor_10 + self.factor_11 +
            self.factor_12 + self.factor_13 + self.factor_14 + self.factor_15 +
            self.factor_16 + self.factor_17 + self.factor_18 + self.factor_19
        )
        
        if suma_factores > Decimal('1.00000000'):
            raise ValidationError(
                f"La suma de los factores del 8 al 19 ({suma_factores}) supera el límite permitido de 1.00000000."
            )

        if self.secuencia <= 10000:
            raise ValidationError("La secuencia de evento debe ser estrictamente mayor a 10000.")

        if self.tipo_sociedad not in ['A', 'C']:
            raise ValidationError("El tipo de sociedad debe ser 'A' o 'C'.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.instrumento.nemotecnico} - Ejercicio {self.ejercicio} - Secuencia {self.secuencia}"


class AuditoriaLog(models.Model):
    id_usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_column='id_usuario')
    fecha_hora = models.DateTimeField(auto_now_add=True)
    accion = models.TextField()
    tipo_operacion = models.CharField(max_length=10)  # 'INSERT', 'UPDATE', 'DELETE'
    datos_previos = models.JSONField(null=True, blank=True, db_column='datos_previos')

    class Meta:
        db_table = 'auditoria_log'
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'

    def __str__(self):
        usuario = self.id_usuario.username if self.id_usuario else "Sistema"
        return f"{self.tipo_operacion} - {usuario} - {self.fecha_hora.strftime('%Y-%m-%d %H:%M:%S')}"


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    cambio_password_obligatorio = models.BooleanField(default=True)

    class Meta:
        db_table = 'perfil_usuario'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'

    def __str__(self):
        return f"Perfil de {self.user.username}"
