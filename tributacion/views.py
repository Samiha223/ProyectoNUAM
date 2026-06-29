import csv
import io
import json
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
from django.db.models import F

from tributacion.models import Mercado, Instrumento, CalificacionTributaria, AuditoriaLog

# Helpers para control de acceso RBAC
def es_administrador(user):
    return user.is_superuser or user.groups.filter(name='Administrador').exists()

def es_corredor(user):
    return user.groups.filter(name='Corredor de Bolsa').exists()

def obtener_datos_serializables(obj):
    """
    Serializa una instancia de CalificacionTributaria a un diccionario para logs.
    """
    if not obj:
        return None
    data = {
        'id': obj.id,
        'ejercicio': obj.ejercicio,
        'mercado_id': obj.mercado_id,
        'mercado_nombre': obj.mercado.nombre,
        'instrumento_id': obj.instrumento_id,
        'instrumento_nemotecnico': obj.instrumento.nemotecnico,
        'fecha_pago': str(obj.fecha_pago),
        'secuencia': obj.secuencia,
        'nro_dividendo': obj.nro_dividendo,
        'tipo_sociedad': obj.tipo_sociedad,
        'valor_historico': str(obj.valor_historico),
        'fuente_ingreso': obj.fuente_ingreso,
    }
    # Agregar factores
    for i in range(8, 38):
        data[f'factor_{i}'] = str(getattr(obj, f'factor_{i}'))
    # Agregar montos
    for i in range(8, 20):
        val = getattr(obj, f'monto_{i}')
        data[f'monto_{i}'] = str(val) if val is not None else None
    return data


def login_usuario(request):
    if request.method == 'POST':
        data = json.loads(request.body) if request.headers.get('Content-Type') == 'application/json' else request.POST
        username = data.get('username')
        password = data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Credenciales inválidas'}, status=400)
    return render(request, 'tributacion/login.html')


def logout_usuario(request):
    logout(request)
    return redirect('login')


@login_required
def index(request):
    mercados = Mercado.objects.all().order_by('nombre')
    instrumentos = Instrumento.objects.all().order_by('nemotecnico')
    rol = 'Administrador' if es_administrador(request.user) else 'Corredor de Bolsa' if es_corredor(request.user) else 'Invitado'
    context = {
        'mercados': mercados,
        'instrumentos': instrumentos,
        'usuario': request.user,
        'rol': rol,
        'es_admin': es_administrador(request.user),
        'rango_8_9': [8, 9],
        'rango_10_19': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
        'rango_20_37': list(range(20, 38)),
    }
    return render(request, 'tributacion/index.html', context)


@login_required
def buscar_calificaciones(request):
    """
    Retorna la lista filtrada de calificaciones tributarias en formato JSON.
    """
    mercado_id = request.GET.get('mercado_id')
    fuente_ingreso = request.GET.get('fuente_ingreso')
    ejercicio = request.GET.get('ejercicio')

    queryset = CalificacionTributaria.objects.select_related('mercado', 'instrumento').all()

    if mercado_id:
        queryset = queryset.filter(mercado_id=mercado_id)
    if fuente_ingreso:
        queryset = queryset.filter(fuente_ingreso=fuente_ingreso)
    if ejercicio:
        queryset = queryset.filter(ejercicio=ejercicio)

    queryset = queryset.order_by('-ejercicio', 'instrumento__nemotecnico', 'secuencia')

    datos = []
    for item in queryset:
        datos.append({
            'id': item.id,
            'ejercicio': item.ejercicio,
            'mercado': item.mercado.nombre,
            'mercado_id': item.mercado_id,
            'instrumento': item.instrumento.nemotecnico,
            'instrumento_id': item.instrumento_id,
            'fecha_pago': str(item.fecha_pago),
            'secuencia': item.secuencia,
            'nro_dividendo': item.nro_dividendo,
            'tipo_sociedad': item.tipo_sociedad,
            'valor_historico': float(item.valor_historico),
            'fuente_ingreso': item.fuente_ingreso,
            'factor_8_19_sum': float(
                item.factor_8 + item.factor_9 + item.factor_10 + item.factor_11 +
                item.factor_12 + item.factor_13 + item.factor_14 + item.factor_15 +
                item.factor_16 + item.factor_17 + item.factor_18 + item.factor_19
            )
        })
    return JsonResponse({'success': True, 'data': datos})


@login_required
@transaction.atomic
def guardar_calificacion(request):
    """
    Guarda o edita un registro de calificación manual.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        registro_id = data.get('id')
        
        # Validar campos requeridos
        ejercicio = int(data.get('ejercicio'))
        mercado_id = int(data.get('mercado_id'))
        instrumento_id = int(data.get('instrumento_id'))
        fecha_pago = parse_date(data.get('fecha_pago'))
        secuencia = int(data.get('secuencia'))
        nro_dividendo = int(data.get('nro_dividendo'))
        tipo_sociedad = data.get('tipo_sociedad')
        valor_historico = Decimal(str(data.get('valor_historico')))

        if not fecha_pago:
            return JsonResponse({'success': False, 'error': 'Fecha de pago inválida'}, status=400)

        mercado = Mercado.objects.get(id=mercado_id)
        instrumento = Instrumento.objects.get(id=instrumento_id)

        # Crear o recuperar instancia
        if registro_id:
            obj = CalificacionTributaria.objects.get(id=registro_id)
            datos_previos = obtener_datos_serializables(obj)
            accion = "Edición manual de Calificación"
            tipo_operacion = "UPDATE"
        else:
            obj = CalificacionTributaria()
            datos_previos = None
            accion = "Creación manual de Calificación"
            tipo_operacion = "INSERT"

        obj.ejercicio = ejercicio
        obj.mercado = mercado
        obj.instrumento = instrumento
        obj.fecha_pago = fecha_pago
        obj.secuencia = secuencia
        obj.nro_dividendo = nro_dividendo
        obj.tipo_sociedad = tipo_sociedad
        obj.valor_historico = valor_historico
        obj.fuente_ingreso = 'Manual'

        # Asignar montos si existen
        tiene_montos = False
        for i in range(8, 20):
            monto_val = data.get(f'monto_{i}')
            if monto_val is not None and str(monto_val).strip() != '':
                setattr(obj, f'monto_{i}', Decimal(str(monto_val)))
                tiene_montos = True
            else:
                setattr(obj, f'monto_{i}', None)

        # Si no tiene montos, asignar factores ingresados manualmente
        if not tiene_montos:
            for i in range(8, 38):
                factor_val = data.get(f'factor_{i}')
                if factor_val is not None and str(factor_val).strip() != '':
                    setattr(obj, f'factor_{i}', Decimal(str(factor_val)))
                else:
                    setattr(obj, f'factor_{i}', Decimal('0.00000000'))
        else:
            # Factores 20 al 37 si es carga con montos
            for i in range(20, 38):
                factor_val = data.get(f'factor_{i}')
                if factor_val is not None and str(factor_val).strip() != '':
                    setattr(obj, f'factor_{i}', Decimal(str(factor_val)))
                else:
                    setattr(obj, f'factor_{i}', Decimal('0.00000000'))

        # Validaciones de integridad y reglas del modelo
        obj.full_clean()
        obj.save()

        # Auditoría Log
        AuditoriaLog.objects.create(
            id_usuario=request.user,
            accion=accion,
            tipo_operacion=tipo_operacion,
            datos_previos=datos_previos
        )

        return JsonResponse({'success': True, 'message': 'Calificación guardada exitosamente'})

    except ValidationError as e:
        return JsonResponse({'success': False, 'error': e.messages[0] if isinstance(e.messages, list) else str(e)}, status=400)
    except IntegrityError as e:
        return JsonResponse({'success': False, 'error': 'Ya existe una calificación con el mismo Ejercicio, Instrumento y Secuencia.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@transaction.atomic
def eliminar_calificacion(request):
    """
    Elimina un registro de calificación y guarda el log de auditoría.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        registro_id = data.get('id')
        if not registro_id:
            return JsonResponse({'success': False, 'error': 'ID del registro no proporcionado'}, status=400)

        obj = CalificacionTributaria.objects.get(id=registro_id)
        datos_previos = obtener_datos_serializables(obj)

        # Eliminar el objeto
        obj.delete()

        # Auditoría Log
        AuditoriaLog.objects.create(
            id_usuario=request.user,
            accion=f"Eliminación de Calificación ({obj.instrumento.nemotecnico} - Seq {obj.secuencia})",
            tipo_operacion="DELETE",
            datos_previos=datos_previos
        )

        return JsonResponse({'success': True, 'message': 'Registro eliminado exitosamente'})

    except CalificacionTributaria.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'El registro no existe'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def previsualizar_csv(request):
    """
    Parsea el CSV recibido en memoria, realiza el cálculo preliminar y retorna los datos para previsualización.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    archivo = request.FILES.get('archivo')
    tipo_carga = request.POST.get('tipo_carga')  # 'factores' o 'montos'

    if not archivo:
        return JsonResponse({'success': False, 'error': 'No se cargó ningún archivo'}, status=400)
    if tipo_carga not in ['factores', 'montos']:
        return JsonResponse({'success': False, 'error': 'Tipo de carga masiva inválido'}, status=400)

    try:
        # Leer el archivo en memoria
        contenido_archivo = archivo.read().decode('utf-8-sig')
        stream = io.StringIO(contenido_archivo)
        lector = csv.DictReader(stream)

        # Columnas obligatorias comunes
        columnas_comunes = ['ejercicio', 'nemotecnico', 'secuencia', 'fecha_pago', 'nro_dividendo', 'tipo_sociedad', 'valor_historico']
        
        # Validar cabeceras básicas
        headers = lector.fieldnames
        for col in columnas_comunes:
            if col not in headers:
                return JsonResponse({'success': False, 'error': f"Falta la columna obligatoria '{col}' en el CSV"}, status=400)

        filas_preview = []
        for nro_fila, fila in enumerate(lector, start=1):
            try:
                ejercicio = int(fila['ejercicio'])
                nemotecnico = fila['nemotecnico'].strip()
                secuencia = int(fila['secuencia'])
                fecha_pago = fila['fecha_pago'].strip()
                nro_dividendo = int(fila['nro_dividendo'])
                tipo_sociedad = fila['tipo_sociedad'].strip().upper()
                valor_historico = Decimal(fila['valor_historico'])

                # Buscar instrumento
                try:
                    instrumento = Instrumento.objects.get(nemotecnico=nemotecnico)
                    instrumento_nombre = instrumento.nombre or nemotecnico
                    mercado_nombre = instrumento.mercado.nombre
                    mercado_id = instrumento.mercado.id
                except Instrumento.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f"Fila {nro_fila}: El instrumento '{nemotecnico}' no existe en el sistema"}, status=400)

                # Validar campos básicos
                if secuencia <= 10000:
                    return JsonResponse({'success': False, 'error': f"Fila {nro_fila}: Secuencia {secuencia} debe ser mayor a 10000"}, status=400)
                if tipo_sociedad not in ['A', 'C']:
                    return JsonResponse({'success': False, 'error': f"Fila {nro_fila}: Tipo de sociedad '{tipo_sociedad}' debe ser 'A' o 'C'"}, status=400)

                factores = {}
                montos = {}

                if tipo_carga == 'montos':
                    # Leer montos 8 al 19
                    suma_montos = Decimal('0.00')
                    for i in range(8, 20):
                        col_name = f'monto_{i}'
                        if col_name not in fila or not fila[col_name]:
                            val_monto = Decimal('0.00')
                        else:
                            val_monto = Decimal(fila[col_name])
                        montos[col_name] = float(val_monto)
                        suma_montos += val_monto
                    
                    # Calcular factores 8 al 19
                    for i in range(8, 20):
                        if suma_montos > 0:
                            factores[f'factor_{i}'] = float(round(Decimal(str(montos[f'monto_{i}'])) / suma_montos, 8))
                        else:
                            factores[f'factor_{i}'] = 0.0
                    
                    # Factores 20 al 37 en cero
                    for i in range(20, 38):
                        factores[f'factor_{i}'] = 0.0
                else:
                    # Carga masiva de factores
                    for i in range(8, 38):
                        col_name = f'factor_{i}'
                        if col_name not in fila or not fila[col_name]:
                            val_factor = Decimal('0.00000000')
                        else:
                            val_factor = Decimal(fila[col_name])
                        factores[col_name] = float(val_factor)

                # Validar suma factores 8 al 19 en previsualización
                suma_factores_8_19 = sum(factores[f'factor_{i}'] for i in range(8, 20))
                if suma_factores_8_19 > 1.00000001:  # tolerancia pequeña por coma flotante en JS
                    return JsonResponse({'success': False, 'error': f"Fila {nro_fila}: La suma de los factores del 8 al 19 ({suma_factores_8_19:.8f}) supera el límite de 1.00000000"}, status=400)

                filas_preview.append({
                    'ejercicio': ejercicio,
                    'nemotecnico': nemotecnico,
                    'instrumento_id': instrumento.id,
                    'instrumento_nombre': instrumento_nombre,
                    'mercado_id': mercado_id,
                    'mercado_nombre': mercado_nombre,
                    'secuencia': secuencia,
                    'fecha_pago': fecha_pago,
                    'nro_dividendo': nro_dividendo,
                    'tipo_sociedad': tipo_sociedad,
                    'valor_historico': float(valor_historico),
                    'factores': factores,
                    'montos': montos if tipo_carga == 'montos' else None
                })

            except (ValueError, InvalidOperation) as e:
                return JsonResponse({'success': False, 'error': f"Fila {nro_fila}: Error en el formato numérico o de fecha. Detalle: {str(e)}"}, status=400)

        return JsonResponse({'success': True, 'data': filas_preview})

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Error al procesar el archivo CSV: {str(e)}"}, status=400)


@login_required
@transaction.atomic
def confirmar_carga_masiva(request):
    """
    Recibe la lista previsualizada y ejecuta la lógica de Upsert atómica sobre la BD.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        payload = json.loads(request.body)
        datos_carga = payload.get('data', [])
        tipo_carga = payload.get('tipo_carga')  # 'factores' o 'montos'

        if not datos_carga:
            return JsonResponse({'success': False, 'error': 'No hay datos para procesar'}, status=400)

        fuente = 'Carga Masiva Factores' if tipo_carga == 'factores' else 'Carga Masiva Montos'
        upserts_count = 0
        inserts_count = 0

        # Para auditar de forma masiva, agruparemos por tipo
        for item in datos_carga:
            ejercicio = int(item['ejercicio'])
            instrumento_id = int(item['instrumento_id'])
            secuencia = int(item['secuencia'])
            mercado_id = int(item['mercado_id'])

            # Buscar si ya existe la clave única (ejercicio, instrumento_id, secuencia)
            existing_obj = CalificacionTributaria.objects.filter(
                ejercicio=ejercicio,
                instrumento_id=instrumento_id,
                secuencia=secuencia
            ).first()

            if existing_obj:
                # Upsert: Actualizar
                datos_previos = obtener_datos_serializables(existing_obj)
                obj = existing_obj
                obj.fecha_pago = parse_date(item['fecha_pago'])
                obj.nro_dividendo = int(item['nro_dividendo'])
                obj.tipo_sociedad = item['tipo_sociedad']
                obj.valor_historico = Decimal(str(item['valor_historico']))
                obj.mercado_id = mercado_id
                obj.fuente_ingreso = fuente
                upserts_count += 1
                tipo_operacion = "UPDATE"
                accion = f"Carga masiva (Actualización) de {fuente}"
            else:
                # Upsert: Crear nuevo
                datos_previos = None
                obj = CalificacionTributaria(
                    ejercicio=ejercicio,
                    instrumento_id=instrumento_id,
                    secuencia=secuencia,
                    mercado_id=mercado_id,
                    fecha_pago=parse_date(item['fecha_pago']),
                    nro_dividendo=int(item['nro_dividendo']),
                    tipo_sociedad=item['tipo_sociedad'],
                    valor_historico=Decimal(str(item['valor_historico'])),
                    fuente_ingreso=fuente
                )
                inserts_count += 1
                tipo_operacion = "INSERT"
                accion = f"Carga masiva (Inserción) de {fuente}"

            # Asignar factores
            for i in range(8, 38):
                val_factor = item['factores'].get(f'factor_{i}', 0.0)
                setattr(obj, f'factor_{i}', Decimal(str(val_factor)))

            # Asignar montos si corresponde
            if item.get('montos'):
                for i in range(8, 20):
                    val_monto = item['montos'].get(f'monto_{i}')
                    setattr(obj, f'monto_{i}', Decimal(str(val_monto)) if val_monto is not None else None)

            # Validar y Guardar
            obj.full_clean()
            obj.save()

            # Guardar en Logs de Auditoría
            AuditoriaLog.objects.create(
                id_usuario=request.user,
                accion=accion,
                tipo_operacion=tipo_operacion,
                datos_previos=datos_previos
            )

        return JsonResponse({
            'success': True,
            'message': f"Carga masiva procesada exitosamente. Nuevos registros: {inserts_count}. Actualizados: {upserts_count}."
        })

    except ValidationError as e:
        return JsonResponse({'success': False, 'error': f"Error de negocio en la carga: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Fallo en la transacción: {str(e)}"}, status=400)


@login_required
def ver_logs(request):
    """
    Retorna la lista de logs de auditoría forense para fines de auditoría del sistema.
    """
    logs = AuditoriaLog.objects.select_related('id_usuario').all().order_by('-fecha_hora')[:50]
    data = []
    for log in logs:
        data.append({
            'id': log.id,
            'fecha_hora': log.fecha_hora.strftime('%Y-%m-%d %H:%M:%S'),
            'usuario': log.id_usuario.username if log.id_usuario else 'Sistema',
            'accion': log.accion,
            'tipo_operacion': log.tipo_operacion,
            'datos_previos': log.datos_previos
        })
    return JsonResponse({'success': True, 'data': data})
