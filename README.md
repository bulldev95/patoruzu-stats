# Patoruzú Stats

App web de estadísticas de rugby en vivo para Patoruzú Rugby Club.  
Permite registrar incidencias durante el partido, ver el marcador en tiempo real y consultar estadísticas históricas de jugadores y equipo.

---

## Requisitos

- **Python 3.11 o superior** — [Descargar desde python.org](https://www.python.org/downloads/)
  - Durante la instalación marcar la opción **"Add Python to PATH"**
- **Git** (solo para clonar el repositorio) — [Descargar desde git-scm.com](https://git-scm.com/download/win)
- Conexión a internet la primera vez (para instalar dependencias)

---

## Instalación

### 1. Descargar el código

Abrí una terminal (CMD o PowerShell) y ejecutá:

```
git clone https://github.com/bulldev95/patoruzu-stats.git
```

O descargá el ZIP desde GitHub → **Code → Download ZIP** y descomprimilo.

### 2. Iniciar la app

Entrá a la carpeta `patoruzu-stats` y hacé **doble clic en `start.bat`**.

La primera vez va a tardar un par de minutos mientras instala las dependencias. Las veces siguientes arranca en segundos.

El navegador se abre automáticamente en `http://localhost:8000`.

**Para cerrar la app:** cerrá la ventana negra que se abrió al hacer doble clic.

---

## Cargar datos de prueba

Si querés explorar la app con datos ficticios (5 partidos ya cargados), ejecutá desde la terminal:

```
venv\Scripts\activate
python seed_mock.py
```

Esto carga jugadores, partidos y estadísticas de ejemplo.

---

## Uso básico

1. **Nuevo partido** → subir PDF del plantel UAR → confirmar jugadores
2. **Vista en vivo** → registrar incidencias, controlar el reloj, hacer sustituciones
3. **Cierre** → al finalizar el partido, cerrar desde el botón "Cerrar partido"
4. **Estadísticas** → `/stats/team` para el equipo, `/stats/players` para jugadores individuales

---

## Solución de problemas

**"Python no está instalado"**  
Instalar Python desde [python.org](https://www.python.org/downloads/) y asegurarse de marcar "Add Python to PATH".

**"El puerto 8000 ya está en uso"**  
La app ya está corriendo. El navegador se abrirá igual. Si no estaba corriendo, reiniciar la PC y volver a intentar.

**"No se pudieron instalar las dependencias"**  
Verificar conexión a internet y volver a hacer doble clic en `start.bat`.

**La ventana negra se cierra sola con un error**  
Abrirla desde la terminal para ver el mensaje de error:
```
cd patoruzu-stats
start.bat
```
