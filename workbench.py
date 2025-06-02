import mysql.connector
import json
from datetime import datetime, timedelta
import requests  # Estoy importando la librería para hacer solicitudes HTTP
import xml.etree.ElementTree as ET  # Estoy importando la librería para procesar datos XML

class Aplicacion:
    def __init__(self, config_db, json_file, api_key):
        """
        Inicializo la aplicación con la configuración de la base de datos, el archivo JSON y la clave de la API.
        :param config_db: Diccionario con la configuración de la base de datos.
        :param json_file: Ruta del archivo JSON que contiene los datos de los países.
        :param api_key: Clave de API para OpenWeatherMap.
        """
        self.config_db = config_db
        self.json_file = json_file
        self.api_key = api_key
        self.conexion = self.conexion_mysql()  # Establezco la conexión a la base de datos
        self.datos = self.leer_datos()  # Leo los datos de los países desde el archivo JSON

    def conexion_mysql(self):
        """
        Establezco la conexión con la base de datos MySQL.
        :return: Objeto de conexión a la base de datos.
        """
        try:
            return mysql.connector.connect(**self.config_db)  # Intento conectar con la base de datos
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")  # Si hay error, lo imprimo
            return None

    def leer_datos(self):
        """
        Leo los datos de los países desde un archivo JSON.
        :return: Diccionario con los datos de los países.
        """
        try:
            with open(self.json_file, "r", encoding="utf-8") as file:
                return json.load(file)  # Leo el archivo JSON y lo convierto a un diccionario
        except Exception as e:
            print(f"Error al leer el archivo: {e}")  # Si hay error al leer, lo imprimo
            return None

    def insertar_datos_pais(self):
        """
        Inserto los datos de los países en la tabla 'paises' de la base de datos.
        """
        if not self.datos:  # Si no tengo datos, imprimo un mensaje y retorno
            print("No hay datos para insertar.")
            return

        cursor = self.conexion.cursor()  # Creo un cursor para interactuar con la base de datos
        for pais in self.datos:  # Itero sobre los países
            try:
                # Determino si pertenece a la Naciones Unidas, si pertenece se guardará como 1, si no como 0
                miembro_ue = 1 if pais.get("unMember", False) else 0

                # Obtengo los valores necesarios del país
                cca2 = pais.get("cca2", "")
                cca3 = pais.get("cca3", "")
                nombre = pais.get("name", {}).get("common", "")
                capital = pais.get("capital", [""])[0] if pais.get("capital") else ""  # Obtengo la capital, si existe
                region = pais.get("region", "")
                subregion = pais.get("subregion", "")
                latitud = pais.get("latlng", [None, None])[0]
                longitud = pais.get("latlng", [None, None])[1]

                # Inserto los datos del país en la base de datos
                cursor.execute(
                    "INSERT INTO paises (cca2, cca3, nombre, capital, region, subregion, latitud, longitud, miembroUE) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (cca2, cca3, nombre, capital, region, subregion, latitud, longitud, miembro_ue),
                )
            except Exception as e:
                print(f"Error al insertar datos: {e}")  # Si hay error al insertar, lo imprimo

        self.conexion.commit()  # Hago commit para guardar los cambios
        print("Datos insertados correctamente en la tabla 'paises'.")

    def insertar_datos_fronteras(self):
        """
        Inserto los datos de las fronteras en la tabla 'fronteras' de la base de datos.
        """
        if not self.datos:  # Si no tengo datos, imprimo un mensaje y retorno
            print("No hay datos para insertar.")
            return

        cursor = self.conexion.cursor()  # Creo un cursor para interactuar con la base de datos
        for pais in self.datos:  # Itero sobre los países
            cca3 = pais.get("cca3", "")
            fronteras = pais.get("borders", [])

            if not cca3:  # Si no tengo el código cca3, salto este país
                print("No se proporcionó un código cca3 para el país")
                continue

            # Obtengo el idpais usando el código cca3
            cursor.execute("SELECT idpais FROM paises WHERE cca3 = %s", (cca3,))
            resultado = cursor.fetchone()
            cursor.fetchall()  # Limpio cualquier resultado pendiente

            if resultado:  # Si encontré el país en la base de datos
                idpais = resultado[0]
                for frontera in fronteras:  # Inserto cada frontera en la tabla 'fronteras'
                    cursor.execute(
                        "INSERT INTO fronteras (idpais, cca3_frontera) VALUES (%s, %s)",
                        (idpais, frontera),
                    )

        # Hago commit para guardar los cambios
        self.conexion.commit()
        print("Datos insertados correctamente en la tabla 'fronteras'.")

    def obtener_temperatura_json(self, capital):
        """
        Obtengo los datos de temperatura de la capital de un país mediante la API OpenWeather en formato JSON.
        :param capital: Nombre de la capital del país.
        :return: Diccionario con los datos de temperatura.
        """
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={capital}&appid={self.api_key}&units=metric"
            response = requests.get(url)

            if response.status_code == 404:  # Si no encuentro datos, imprimo un mensaje indicando que no se ha encontrado
                print(f"No se encontraron datos climáticos para {capital}.")
                return None

            if response.status_code != 200:  # Si ocurre otro error, lo imprimo
                print(f"Error al obtener los datos climáticos para {capital}: {response.status_code}")
                return None

            data = response.json()  # Convierto la respuesta a JSON
            print(f"Respuesta JSON completa: {data}")  # Imprimo la respuesta para depuración

            # Verifico si el campo 'dt' está presente en la respuesta
            if 'dt' not in data:
                print(f"No se encontró el timestamp para {capital} (JSON).")
                return None

            # Extraigo los datos de tiempo
            dt = data.get("dt")
            sunrise_ts = data.get("sys", {}).get("sunrise")
            sunset_ts = data.get("sys", {}).get("sunset")

            # Convierto strings a datetime
            timestamp = datetime.fromtimestamp(dt) if dt else None
            sunrise = datetime.fromtimestamp(sunrise_ts) if sunrise_ts else None
            sunset = datetime.fromtimestamp(sunset_ts) if sunset_ts else None

            # Verifico si la conversión fue exitosa
            if timestamp is None:
                print(f"Timestamp inválido para {capital}.")
                return None

            # Creo un diccionario con los datos del clima
            clima = {
                "temperature": data["main"].get("temp", 0),
                "feels_like": data["main"].get("feels_like", 0),
                "temp_min": data["main"].get("temp_min", 0),
                "temp_max": data["main"].get("temp_max", 0),
                "humidity": data["main"].get("humidity", 0),
                "sunrise": sunrise,
                "sunset": sunset,
                "timestamp": timestamp,
            }
            return clima
        except Exception as e:
            print(f"Error al obtener datos JSON para {capital}: {e}")  # Si hay error, lo imprimo
            return None

    def obtener_temperatura_xml(self, capital):
        """
        Obtengo los datos de temperatura de la capital de un país mediante la API OpenWeather en formato XML.
        :param capital: Nombre de la capital del país.
        :return: Diccionario con los datos de temperatura.
        """
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={capital}&appid={self.api_key}&units=metric&mode=xml"
            response = requests.get(url)

            if response.status_code == 404:  # Si no encuentro datos, imprimo un mensaje
                print(f"No se encontraron datos climáticos para {capital}.")
                return None

            if response.status_code != 200:  # Si ocurre otro error, lo imprimo
                print(f"Error al obtener los datos climáticos para {capital}: {response.status_code}")
                return None

            root = ET.fromstring(response.content)  # Convierto la respuesta XML en un objeto ElementTree
            print(f"Respuesta XML completa: {ET.tostring(root)}")  # Imprimo la respuesta para depuración

            # Verifico si el campo 'lastupdate' está presente en la respuesta
            lastupdate_elem = root.find(".//lastupdate")
            if lastupdate_elem is None:
                print(f"No se encontró el timestamp para {capital} (XML).")
                return None

            lastupdate_str = lastupdate_elem.get("value")  # Fecha en formato string
            sunrise_str = root.find(".//city/sun").get("rise") if root.find(".//city/sun") is not None else None
            sunset_str = root.find(".//city/sun").get("set") if root.find(".//city/sun") is not None else None

            # Convierto strings a datetime
            timestamp = datetime.strptime(lastupdate_str, "%Y-%m-%dT%H:%M:%S") if lastupdate_str else None
            sunrise = datetime.strptime(sunrise_str, "%Y-%m-%dT%H:%M:%S") if sunrise_str else None
            sunset = datetime.strptime(sunset_str, "%Y-%m-%dT%H:%M:%S") if sunset_str else None

            # Verifico si la conversión fue exitosa
            if timestamp is None:
                print(f"Timestamp inválido para {capital} (XML).")
                return None

            # Creo un diccionario con los datos del clima
            clima = {
                "temperature": float(root.find(".//temperature").get("value")),
                "feels_like": float(root.find(".//feels_like").get("value")),
                "temp_min": float(root.find(".//temperature").get("min")),
                "temp_max": float(root.find(".//temperature").get("max")),
                "humidity": float(root.find(".//humidity").get("value")),
                "sunrise": sunrise,
                "sunset": sunset,
                "timestamp": timestamp,
            }
            return clima
        except Exception as e:
            print(f"Error al obtener datos XML para {capital}: {e}")  # Si hay error, lo imprimo
            return None

    def insertar_datos_temperaturas(self):
        """
        Inserto las temperaturas obtenidas mediante las APIs (JSON y XML).
        """
        if not self.datos:  # Si no tengo datos de países, imprimo un mensaje y retorno
            print("No hay datos de países disponibles para insertar temperaturas.")
            return

        cursor = self.conexion.cursor(dictionary=True)  # Creo un cursor para interactuar con la base de datos
        paises_europeos = [pais for pais in self.datos if pais.get("region") == "Europe"]  # Filtrar países de Europa
        mitad = len(paises_europeos) // 2  # Divido la lista en dos mitades
        paises_json = paises_europeos[:mitad]
        paises_xml = paises_europeos[mitad:]

        # Procesar países con JSON
        for pais in paises_json:
            capital = pais.get("capital", [""])[0]  # Obtengo la capital del país
            if not capital:
                continue
            clima_json = self.obtener_temperatura_json(capital)  # Obtengo el clima en formato JSON
            if clima_json and isinstance(clima_json, dict):
                try:
                    timestamp = clima_json.get("timestamp")
                    if not timestamp:
                        print(f"Timestamp no disponible para {capital} (JSON). Saltando...")  # Si no hay timestamp, salto este país
                        continue

                    # Obtengo el idpais usando el código cca3
                    cursor.execute("SELECT idpais FROM paises WHERE cca3 = %s", (pais["cca3"],))
                    resultado = cursor.fetchone()
                    cursor.fetchall()  # Limpiar resultados

                    if not resultado:  # Si no encuentro el país, imprimo un mensaje
                        print(f"No se encontró idpais para {capital}.")
                        continue

                    idpais = resultado["idpais"]
                    cursor.execute(
                        """INSERT INTO temperaturas 
                        (idpais, timestamp, temperatura, sensacion, minima, maxima, humedad, amanecer, atardecer) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            idpais,
                            timestamp,
                            clima_json.get("temperature", 0),
                            clima_json.get("feels_like", 0),
                            clima_json.get("temp_min", 0),
                            clima_json.get("temp_max", 0),
                            clima_json.get("humidity", 0),
                            clima_json.get("sunrise"),
                            clima_json.get("sunset"),
                        ),
                    )  # Insertamos la mitad de los datos a la tabla 'temperaturas'
                except Exception as e:
                    print(f"Error al procesar datos de temperatura para {capital} (JSON): {e}")  # Si hay error al insertar, lo imprimo

        # Procesar países con XML
        for pais in paises_xml:
            capital = pais.get("capital", [""])[0]  # Obtengo la capital del país
            if not capital:
                continue
            clima_xml = self.obtener_temperatura_xml(capital)  # Obtengo el clima en formato XML
            if clima_xml and isinstance(clima_xml, dict):
                try:
                    timestamp = clima_xml.get("timestamp")
                    if not timestamp:
                        print(f"Timestamp no disponible para {capital} (XML). Saltando...")  # Si no hay timestamp, salto este país
                        continue

                    # Obtengo el idpais usando el código cca3
                    cursor.execute("SELECT idpais FROM paises WHERE cca3 = %s", (pais["cca3"],))
                    resultado = cursor.fetchone()
                    cursor.fetchall()  # Limpiar resultados

                    if not resultado:  # Si no encuentro el país, imprimo un mensaje
                        print(f"No se encontró idpais para {capital}.")
                        continue

                    idpais = resultado["idpais"]
                    cursor.execute(
                        """INSERT INTO temperaturas 
                        (idpais, timestamp, temperatura, sensacion, minima, maxima, humedad, amanecer, atardecer) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            idpais,
                            timestamp,
                            clima_xml.get("temperature", 0),
                            clima_xml.get("feels_like", 0),
                            clima_xml.get("temp_min", 0),
                            clima_xml.get("temp_max", 0),
                            clima_xml.get("humidity", 0),
                            clima_xml.get("sunrise"),
                            clima_xml.get("sunset"),
                        ),
                    )  # Insertamos la mitad de los datos a la tabla 'temperaturas'
                except Exception as e:
                    print(f"Error al procesar datos de temperatura para {capital} (XML): {e}")  # Si hay error al insertar, lo imprimo

        self.conexion.commit()  # Hago commit para guardar los cambios
        print("Datos de temperaturas insertados correctamente.")



    def mostrar_paises(self):
        """Muestra los datos de la tabla 'paises'."""
        cursor = self.conexion.cursor(dictionary=True)
        print("\n📌 Tabla: PAISES")
        cursor.execute("SELECT * FROM paises;")
        paises = cursor.fetchall()
        for pais in paises:
            print(pais)

    def mostrar_fronteras(self):
        """Mostraremos los datos de la tabla 'fronteras'."""
        cursor = self.conexion.cursor(dictionary=True)
        print("\n📌 Tabla: FRONTERAS")
        cursor.execute("SELECT * FROM fronteras;")
        fronteras = cursor.fetchall()
        for frontera in fronteras:
            print(frontera)

    def mostrar_temperaturas(self):
        """Mostrarenos los datos de la tabla 'temperaturas'."""
        cursor = self.conexion.cursor(dictionary=True)
        print("\n📌 Tabla: TEMPERATURAS")
        
        cursor.execute("SELECT * FROM temperaturas;")
        temperaturas = cursor.fetchall()

        # Convertir los campos 'amanecer' y 'atardecer' de timedelta a un formato legible
        for temperatura in temperaturas:
            if isinstance(temperatura['amanecer'], timedelta):
                temperatura['amanecer'] = str(temperatura['amanecer'])  # Convertir a string, ej. '01:28:45'
            if isinstance(temperatura['atardecer'], timedelta):
                temperatura['atardecer'] = str(temperatura['atardecer'])  # Convertir a string

            print(temperatura)  # Ver los datos con los campos convertidos

        return temperaturas  # Devolvemos la lista de temperaturas con los datos procesados

    def mostrar_temperaturas_fronteras(self):
        """Mostraremos las temperaturas de los países fronterizos."""
        cursor = self.conexion.cursor(dictionary=True)
        print("\n📌 Temperaturas de las Fronteras")
        consulta = """
        SELECT 
            f.idpais AS 'ID País Base', 
            f.cca3_frontera AS 'Código Frontera',
            p.nombre AS 'Nombre Frontera',
            t.temperatura, 
            t.sensacion, 
            t.minima, 
            t.maxima, 
            t.humedad, 
            t.amanecer, 
            t.atardecer
        FROM fronteras f
        JOIN paises p ON f.cca3_frontera = p.cca3
        JOIN temperaturas t ON p.idpais = t.idpais;
        """
        cursor.execute(consulta)
        temperaturas_fronteras = cursor.fetchall()
        for temp_frontera in temperaturas_fronteras:
            print(temp_frontera)

    def mostrar_datos_temperaturas_fronteras(self, conexion, idpais):
        """Mostraremos la temperatura del pais introducido y los paises fronterizos de ese pais mas las temperaturas
        de esos paises fronterizos."""
        try:
            cursor = conexion.cursor(dictionary=True)

            # 1. Obtener la información climática del país dado
            cursor.execute("""
                SELECT t.temperatura, t.sensacion, t.minima, t.maxima, 
                    t.humedad, t.amanecer, t.atardecer
                FROM temperaturas t
                WHERE t.idpais = %s
                ORDER BY t.timestamp DESC LIMIT 1  -- Última temperatura registrada
            """, (idpais,))
            
            temp_pais = cursor.fetchone()
            datos_pais = temp_pais if temp_pais else {
                "temperatura": None, "sensacion": None, "minima": None, "maxima": None,
                "humedad": None, "amanecer": None, "atardecer": None
            }

            # 2. Obtener las fronteras del país
            cursor.execute("""
                SELECT f.cca3_frontera, p.nombre AS pais_frontera, p.idpais
                FROM fronteras f
                JOIN paises p ON f.cca3_frontera = p.cca3
                WHERE f.idpais = %s
            """, (idpais,))

            fronteras = cursor.fetchall()
            if not fronteras:
                return {"error": "No se encontraron fronteras para este país.", "pais": datos_pais}

            # Limpiar cualquier resultado pendiente
            cursor.nextset()

            # 3. Obtener las temperaturas de los países fronterizos
            for frontera in fronteras:
                cursor.execute("""
                    SELECT t.temperatura
                    FROM temperaturas t
                    WHERE t.idpais = %s
                    ORDER BY t.timestamp DESC LIMIT 1  -- Última temperatura registrada
                """, (frontera['idpais'],))

                temp_frontera = cursor.fetchone()
                frontera['temperatura'] = temp_frontera['temperatura'] if temp_frontera else None

            cursor.close()

            return {"pais": datos_pais, "fronteras": fronteras}

        except Exception as e:
            return {"error": str(e)}

def main():
    """
    Función principal para ejecutar la aplicación.
    """
    config_db = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "passwd": "caicedo19",
        "database": "temperaturas",
    }
    json_file = "europa_paises.json" # configuro la ruta del archivo JSON con los datos de los países
    api_key = "a60fef3fc371c50c0c57c17361925fad" # establecemos Clave de API para OpenWeatherMap.

    app = Aplicacion(config_db, json_file, api_key) # creamos una instancion de la clase Aplicacion
    app.insertar_datos_pais() # insertamos los datos de los países
    app.insertar_datos_fronteras() # insertamos los datos de las fronteras
    app.insertar_datos_temperaturas() # insertamos los datos de las temperaturas

    # Llamadas a cada método para mostrar las tablas por separado
    app.mostrar_paises()
    app.mostrar_fronteras()
    app.mostrar_temperaturas()
    app.mostrar_temperaturas_fronteras()
    app.mostrar_datos_temperaturas_fronteras()

    app.conexion.close() # cerramos la conexion de la base de datos

if __name__ == "__main__":
    main()