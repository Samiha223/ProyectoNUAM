from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
import datetime

from tributacion.models import Mercado, Instrumento, CalificacionTributaria, AuditoriaLog

class TributacionTestCase(TestCase):

    def setUp(self):
        # Configurar datos de prueba
        self.mercado = Mercado.objects.create(nombre="Acciones Test")
        self.instrumento = Instrumento.objects.create(
            nemotecnico="TEST_INST",
            nombre="Instrumento de Prueba",
            mercado=self.mercado,
            inscrito=True
        )
        self.user = User.objects.create_user(username="testuser", password="password123")

    def test_calculo_factores_desde_montos(self):
        # 100 / 400 = 0.25, 300 / 400 = 0.75
        calif = CalificacionTributaria(
            ejercicio=2024,
            mercado=self.mercado,
            instrumento=self.instrumento,
            fecha_pago=datetime.date(2024, 6, 17),
            secuencia=12000,
            nro_dividendo=1,
            tipo_sociedad='A',
            valor_historico=Decimal('1000.00'),
            fuente_ingreso='Manual',
            monto_8=Decimal('100.00'),
            monto_9=Decimal('300.00')
        )
        calif.save()
        
        # Verificar cálculos
        self.assertEqual(calif.factor_8, Decimal('0.25000000'))
        self.assertEqual(calif.factor_9, Decimal('0.75000000'))
        self.assertEqual(calif.factor_10, Decimal('0.00000000'))

    def test_validacion_suma_factores_excede_limite(self):
        # 0.8 + 0.3 = 1.1 (Excede el límite de 1.0)
        calif = CalificacionTributaria(
            ejercicio=2024,
            mercado=self.mercado,
            instrumento=self.instrumento,
            fecha_pago=datetime.date(2024, 6, 17),
            secuencia=12000,
            nro_dividendo=1,
            tipo_sociedad='A',
            valor_historico=Decimal('1000.00'),
            fuente_ingreso='Manual',
            factor_8=Decimal('0.80000000'),
            factor_9=Decimal('0.30000000')
        )
        
        with self.assertRaises(ValidationError):
            calif.save()

    def test_validacion_secuencia_minima(self):
        # Secuencia debe ser estrictamente > 10000
        calif = CalificacionTributaria(
            ejercicio=2024,
            mercado=self.mercado,
            instrumento=self.instrumento,
            fecha_pago=datetime.date(2024, 6, 17),
            secuencia=9999,
            nro_dividendo=1,
            tipo_sociedad='A',
            valor_historico=Decimal('1000.00'),
            fuente_ingreso='Manual',
            factor_8=Decimal('1.00000000')
        )
        
        with self.assertRaises(ValidationError):
            calif.save()

    def test_validacion_tipo_sociedad_invalido(self):
        calif = CalificacionTributaria(
            ejercicio=2024,
            mercado=self.mercado,
            instrumento=self.instrumento,
            fecha_pago=datetime.date(2024, 6, 17),
            secuencia=12000,
            nro_dividendo=1,
            tipo_sociedad='Z',  # Debe ser A o C
            valor_historico=Decimal('1000.00'),
            fuente_ingreso='Manual',
            factor_8=Decimal('1.00000000')
        )
        
        with self.assertRaises(ValidationError):
            calif.save()

    def test_llave_unica_duplicada(self):
        # Primer registro
        calif1 = CalificacionTributaria.objects.create(
            ejercicio=2024,
            mercado=self.mercado,
            instrumento=self.instrumento,
            fecha_pago=datetime.date(2024, 6, 17),
            secuencia=12000,
            nro_dividendo=1,
            tipo_sociedad='A',
            valor_historico=Decimal('1000.00'),
            fuente_ingreso='Manual',
            factor_8=Decimal('1.00000000')
        )
        
        # Intentar duplicar la combinación (ejercicio, instrumento, secuencia)
        calif2 = CalificacionTributaria(
            ejercicio=2024,
            mercado=self.mercado,
            instrumento=self.instrumento,
            fecha_pago=datetime.date(2024, 6, 18),
            secuencia=12000,
            nro_dividendo=2,
            tipo_sociedad='C',
            valor_historico=Decimal('500.00'),
            fuente_ingreso='Manual',
            factor_8=Decimal('1.00000000')
        )
        
        with self.assertRaises((ValidationError, IntegrityError)):
            # save() llamará a clean() pero para validar duplicidad a nivel BD
            # Django levantará una IntegrityError o ValidationError al guardar.
            calif2.save()

    def test_auditoria_logs_flujo_completo(self):
        # 1. Test Inserción
        calif = CalificacionTributaria.objects.create(
            ejercicio=2024,
            mercado=self.mercado,
            instrumento=self.instrumento,
            fecha_pago=datetime.date(2024, 6, 17),
            secuencia=15000,
            nro_dividendo=1,
            tipo_sociedad='A',
            valor_historico=Decimal('1000.00'),
            fuente_ingreso='Manual',
            factor_8=Decimal('1.00000000')
        )
        # Crear log de inserción manualmente (como en la vista)
        log_ins = AuditoriaLog.objects.create(
            id_usuario=self.user,
            accion="Creación manual",
            tipo_operacion="INSERT",
            datos_previos=None
        )
        self.assertEqual(AuditoriaLog.objects.filter(tipo_operacion="INSERT").count(), 1)
        self.assertNil = self.assertIsNone(log_ins.datos_previos)

        # 2. Test Modificación
        # Capturamos datos previos
        from tributacion.views import obtener_datos_serializables
        datos_previos = obtener_datos_serializables(calif)
        
        calif.valor_historico = Decimal('2000.00')
        calif.save()
        
        log_upd = AuditoriaLog.objects.create(
            id_usuario=self.user,
            accion="Edición manual",
            tipo_operacion="UPDATE",
            datos_previos=datos_previos
        )
        
        self.assertEqual(AuditoriaLog.objects.filter(tipo_operacion="UPDATE").count(), 1)
        self.assertIsNotNone(log_upd.datos_previos)
        self.assertEqual(log_upd.datos_previos['valor_historico'], '1000.00')
