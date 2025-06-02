from flask import Flask, render_template, request
from workbench import Aplicacion  # Importo la clase Aplicacion

# Configuración de la base de datos
config_db = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "passwd": "caicedo19",
    "database": "temperaturas",
}

json_file = "europa_paises.json"  # Ruta del archivo JSON
api_key = "a60fef3fc371c50c0c57c17361925fad"  # Clave de API de OpenWeatherMap

app = Flask(__name__)  # Creo la instancia de Flask

# Inicializo la clase Aplicacion
aplicacion = Aplicacion(config_db, json_file, api_key)

@app.route('/')
def index():
    """
    Esta es la ruta principal que renderiza la página de inicio.
    """
    return render_template('index.html')

@app.route('/insertar')
def insertar():
    """
    Esta ruta me lleva a la página donde puedo insertar los datos de
    países, fronteras y temperaturas en la base de datos.
    """
    return render_template('insertar_tablas.html')

@app.route('/insertar_datos', methods=['POST'])
def insertar_datos():
    """
    Esta ruta se encarga de insertar los datos de países, fronteras y
    temperaturas en la base de datos. Si todo va bien, muestra un mensaje
    de éxito; de lo contrario, muestra un mensaje de error.
    """
    try:
        # Llamo a las funciones para insertar los datos de países, fronteras y temperaturas
        aplicacion.insertar_datos_pais()         # Insertar países
        aplicacion.insertar_datos_fronteras()    # Insertar fronteras
        aplicacion.insertar_datos_temperaturas() # Insertar temperaturas

        mensaje = 'Datos de países, fronteras y temperaturas insertados correctamente.'
        tipo_mensaje = 'success'
    except Exception as e:
        mensaje = f'Error al insertar los datos: {e}'
        tipo_mensaje = 'danger'

    return render_template('insertar_tablas.html', mensaje=mensaje, tipo_mensaje=tipo_mensaje)

@app.route('/mostrar')
def mostrar():
    """
    Esta ruta me permite ver las temperaturas obtenidas de la base de datos.
    Si no encuentro ninguna temperatura, intento obtenerla desde la API.
    """
    try:
        # Intento obtener las temperaturas desde la base de datos
        temperaturas = aplicacion.mostrar_temperaturas()
        print(f"Temperaturas obtenidas desde la base de datos: {temperaturas}")

        if not temperaturas:  # Si no hay temperaturas, las obtengo desde la API
            print("No hay temperaturas, obteniendo desde la API...")

        return render_template('mostrar_tablas_temperaturas.html', temperaturas=temperaturas)

    except Exception as e:
        mensaje = f'Error al obtener las temperaturas: {e}'
        tipo_mensaje = 'danger'
        return render_template('mostrar_tablas_temperaturas.html', mensaje=mensaje, tipo_mensaje=tipo_mensaje)

@app.route('/obtener_temperaturas')
def obtener_temperaturas():
    """
    Esta ruta me permite obtener las temperaturas de la API de OpenWeatherMap
    y almacenarlas en la base de datos. Al final, me muestra un mensaje de éxito
    o de error dependiendo del resultado.
    """
    try:
        # Llamo a la función que obtiene las temperaturas de la API
        aplicacion.obtener_temperaturas_api()

        # Mensaje de éxito
        mensaje = "Temperaturas obtenidas y almacenadas correctamente."
        tipo_mensaje = "success"
    except Exception as e:
        # Si hay un error, muestro un mensaje de error
        mensaje = f"Error al obtener las temperaturas: {e}"
        tipo_mensaje = "danger"

    return render_template('insertar_tablas.html', mensaje=mensaje, tipo_mensaje=tipo_mensaje)

@app.route('/busqueda')
def busqueda():
    """
    Esta ruta me lleva a la página donde puedo realizar la búsqueda de fronteras
    y temperaturas de un país específico.
    """
    return render_template('busqueda_pais.html')

@app.route('/buscar_fronteras', methods=['POST'])
def buscar_fronteras():
    """
    En esta ruta busco un país y sus fronteras con las temperaturas asociadas.
    Si el país se encuentra en la base de datos, me muestra la información del
    país base y sus fronteras. Si ocurre algún error, lo manejo y muestro un mensaje.
    """
    try:
        # 1. Obtengo el nombre del país desde el formulario
        nombre_pais = request.form.get('pais', '').strip()
        if not nombre_pais:
            return render_template('busqueda_pais.html', mensaje="Por favor, ingresa el nombre de un país.")

        print(f"Buscando país: {nombre_pais}")  # Depuración

        # 2. Busco el país en la base de datos
        with aplicacion.conexion.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT idpais, nombre FROM paises WHERE nombre LIKE %s", (f'%{nombre_pais}%',))
            pais = cursor.fetchone()

            if not pais:
                print(f"No se encontró el país: {nombre_pais}")  # Depuración
                return render_template('busqueda_pais.html', mensaje=f"No se encontró el país: {nombre_pais}")

            idpais = pais['idpais']
            nombre_pais_base = pais['nombre']
            print(f"País encontrado: {nombre_pais_base} (ID: {idpais})")  # Depuración

            # 3. Obtengo la información climática del país base y las fronteras con temperaturas
            resultados = aplicacion.mostrar_datos_temperaturas_fronteras(aplicacion.conexion, idpais)
            print(f"Resultados de fronteras: {resultados}")  # Depuración

            if "error" in resultados:
                print(f"Error en mostrar_datos_temperaturas_fronteras: {resultados['error']}")  # Depuración
                return render_template('busqueda_pais.html', mensaje=resultados["error"])

            # 4. Extraigo los datos climáticos del país base
            datos_pais = resultados.get("pais", {})
            temperatura_pais = datos_pais.get("temperatura", "No disponible")
            sensacion_pais = datos_pais.get("sensacion", "No disponible")
            minima_pais = datos_pais.get("minima", "No disponible")
            maxima_pais = datos_pais.get("maxima", "No disponible")
            humedad_pais = datos_pais.get("humedad", "No disponible")
            amanecer_pais = datos_pais.get("amanecer", "No disponible")
            atardecer_pais = datos_pais.get("atardecer", "No disponible")

            # 5. Obtengo la lista de países fronterizos con sus temperaturas
            fronteras = resultados.get("fronteras", [])

            # 6. Muestro los resultados en la plantilla
            return render_template(
                'busqueda_pais.html',
                pais_base=nombre_pais_base,
                temperatura_pais=temperatura_pais,
                sensacion_pais=sensacion_pais,
                minima_pais=minima_pais,
                maxima_pais=maxima_pais,
                humedad_pais=humedad_pais,
                amanecer_pais=amanecer_pais,
                atardecer_pais=atardecer_pais,
                fronteras=fronteras,  # Ahora incluye temperatura de cada frontera
                mensaje=None
            )

    except Exception as e:
        print(f"Error en buscar_fronteras: {e}")  # Depuración
        return render_template('busqueda_pais.html', mensaje=f"Error al procesar la solicitud: {e}")

    
if __name__ == '__main__':
    app.run(debug=True)

