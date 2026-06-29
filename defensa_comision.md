# Guía de Defensa ante la Comisión Examinadora
## Sistema de Gestión Tributaria Local (Corredora de Bolsa)

Este documento sirve de guía técnica paso a paso para preparar y defender el software desarrollado ante la comisión examinadora del proyecto integrado.

---

## 1. Arquitectura de Software y Decisiones de Diseño

El sistema está diseñado bajo el patrón **MVT (Model-View-Template)** de Django combinando una arquitectura orientada a servicios asíncronos en el frontend (AJAX/Fetch) y un modelo de persistencia híbrido en PostgreSQL:

*   **Integridad Referencial Estricta:** Las entidades fijas del negocio bursátil (`Mercado` e `Instrumento`) operan como tablas relacionales con restricciones `ForeignKey` de tipo `PROTECT`. Esto evita la eliminación accidental de un mercado o instrumento si existen calificaciones tributarias históricas asociadas a él.
*   **Modelo de Datos Híbrido:** La tabla de auditoría (`AuditoriaLog`) utiliza un campo **`JSONB`** (`datos_previos`) para almacenar el payload histórico de los registros modificados o eliminados. Esto permite una auditoría forense de datos sin alterar la estructura fija de las tablas relacionales principales.
*   **Reglas de Negocio en la Base de Datos:** Se implementaron restricciones a nivel de base de datos utilizando `CheckConstraint`. La regla más crítica es `chk_suma_factores`, la cual valida físicamente que la suma de los factores del 8 al 19 no pueda ser superior a $1.00000000$. Adicionalmente, se restringe que la secuencia de evento sea $> 10000$ y el tipo de sociedad sea únicamente 'A' o 'C'.

---

## 2. Flujo del Código y Reglas Financieras Chilenas

### Módulo A: Mantenedor Principal (Grilla y Filtros AJAX)
*   **Componente:** `buscar_calificaciones` (en [views.py](file:///c:/Users/Samiha/Desktop/proyecto%20NUAM/tributacion/views.py#L86-L127)) y Grilla HTML (en [index.html](file:///c:/Users/Samiha/Desktop/proyecto%20NUAM/tributacion/templates/tributacion/index.html)).
*   **Funcionamiento:** Al presionar "Buscar", JavaScript realiza una petición asíncrona (`Fetch`) pasando como parámetros `mercado_id`, `fuente_ingreso` y `ejercicio`. La vista de Django recupera los registros ordenados jerárquicamente por ejercicio e instrumento y devuelve un objeto JSON. La tabla se refresca dinámicamente en el DOM sin recargar la página.

### Módulo B: Cálculo y Validación de Factores
*   **Componente:** `clean()` y `save()` en [models.py](file:///c:/Users/Samiha/Desktop/proyecto%20NUAM/tributacion/models.py#L115-L160).
*   **Regla Financiera (DJ1948):** Si el usuario ingresa **Montos** ($M_8$ al $M_{19}$), el sistema los suma para obtener el monto total. Luego, divide cada monto individual por la suma total para obtener el factor correspondiente, aplicando un redondeo estricto a 8 decimales (`round(monto_i / suma_total, 8)`).
*   **Validación:** Tanto en el frontend (vía Javascript) como en el backend (vía Django Models `ValidationError`), si la suma de los factores del 8 al 19 supera $1.00000000$, la transacción se detiene, se muestra un mensaje de error explícito y se bloquea la persistencia.

### Módulo C: Carga Masiva (CSV) y Lógica de *Upsert*
*   **Componente:** `previsualizar_csv` y `confirmar_carga_masiva` (en [views.py](file:///c:/Users/Samiha/Desktop/proyecto%20NUAM/tributacion/views.py#L267-L487)).
*   **Flujo de Carga:**
    1.  **Carga del archivo:** El usuario sube un archivo plano CSV y selecciona el tipo de carga (Factores o Montos).
    2.  **Previsualización en memoria:** Django lee el archivo mediante `StringIO` y `DictReader`. No escribe directamente en la base de datos. Resuelve los nemotécnicos de los instrumentos, realiza el cálculo de factores (si la carga es por montos), valida la consistencia y devuelve las filas formateadas al modal de previsualización.
    3.  **Lógica de Upsert Atómica:** Al confirmar la carga, Django ejecuta una transacción atómica (`@transaction.atomic`). Utiliza la llave única `(ejercicio, instrumento_id, secuencia)` para buscar coincidencias. Si el registro existe, guarda una copia del estado previo en el log de auditoría (tipo `UPDATE`) y sobrescribe los valores. Si no existe, realiza un `INSERT` limpio.

### Módulo D: Logs de Auditoría Forense (Historial de Cambios)
*   **Componente:** `AuditoriaLog` (en [models.py](file:///c:/Users/Samiha/Desktop/proyecto%20NUAM/tributacion/models.py#L166-L181)).
*   **Funcionamiento:** Cada inserción, edición o eliminación genera un registro histórico obligatorio en la base de datos indicando el usuario ejecutor, marca temporal, acción realizada, tipo de operación e historial de datos previos (`JSONB`). Es posible visualizar este payload estructurado directamente desde el menú "Ver Auditoría Logs" del Dashboard.

---

## 3. Guía de Ejecución y Pruebas del Proyecto

### Requisitos Previos
Las dependencias requeridas se encuentran en el sistema (`Django` y `python-dotenv`). El backend posee un mecanismo de fallback inteligente que detecta si PostgreSQL está levantado localmente; en caso de que no responda o no esté configurado, el sistema utilizará SQLite de forma automática para permitir pruebas inmediatas sin errores de infraestructura.

### Paso 1: Aplicar Migraciones
Ejecuta las migraciones de Django para crear la estructura de base de datos:
```bash
python manage.py migrate
```

### Paso 2: Poblar Datos Iniciales (Seed)
Ejecuta el script de poblamiento para precargar los mercados (Acciones, CFI, Fondos Mutuos), instrumentos reales (CHILE, COPEC, CFIMRCLP, etc.) y los usuarios de prueba con roles RBAC asignados:
```bash
python seed.py
```

### Paso 3: Ejecutar Servidor Local
Inicia el servidor de desarrollo de Django:
```bash
python manage.py runserver
```
Accede desde tu navegador en: `http://127.0.0.1:8000/`

### Paso 4: Ejecutar Pruebas Unitarias
Para demostrar a la comisión la cobertura de código y robustez de las reglas de negocio implementadas, ejecuta:
```bash
python manage.py test
```

---

## 4. Respuestas Clave para la Defensa

1.  **¿Por qué se implementó la restricción de suma de factores en la base de datos y no solo en el frontend?**
    *   *Respuesta:* Por principio de defensa en profundidad. Las validaciones de frontend son fácilmente eludibles (por ejemplo, modificando la petición con herramientas de desarrollador o usando scripts externos). Implementar un `CheckConstraint` a nivel de base de datos y validarlo en el backend (`full_clean()`) garantiza que bajo ninguna circunstancia ingresen datos inconsistentes al libro tributario.
2.  **¿Qué ventajas aporta el campo JSONB en la tabla de auditoría en PostgreSQL?**
    *   *Respuesta:* Aporta flexibilidad y rendimiento. En lugar de diseñar tablas de historial complejas por cada entidad o concatenar cadenas de texto difíciles de consultar, `JSONB` almacena el registro completo modificado/eliminado en un formato estructurado y binario de lectura rápida. Esto facilita búsquedas directas dentro del JSON en auditorías posteriores utilizando operadores nativos de PostgreSQL.
3.  **¿Cómo se maneja la consistencia de datos cuando una fila en la carga masiva falla?**
    *   *Respuesta:* La confirmación de carga masiva está envuelta en un bloque de transacción atómica de Django (`@transaction.atomic`). Si una sola fila del archivo CSV viola alguna restricción de validación (por ejemplo, secuencia $\le 10000$ o suma de factores $> 1$), la base de datos realiza un rollback completo de toda la operación, impidiendo que el archivo sea procesado de forma parcial.
