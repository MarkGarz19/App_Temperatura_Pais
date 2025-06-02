# Proyecto: Temperaturas y Fronteras

Este proyecto obtiene y muestra información sobre las temperaturas actuales de los países de Europa, así como las fronteras entre los países, utilizando una base de datos MySQL Workbench y APIs externas (JSON y XML) para la obtención de datos climáticos.

Y consta de dos archivos principales que son fundamentales para su funcionamiento:

- **workbench.py**: Este archivo contiene la lógica para interactuar con la base de datos MySQL llamada temperaturas. Su propósito es almacenar y recuperar información relacionada con los países de Europa, sus fronteras y las temperaturas actuales. Los datos se obtienen de las APIs externas (en formato JSON y XML), así como del archivo europa_paises.json. La base de datos temperaturas consta de tres tablas: paises, fronteras y temperaturas, donde se almacenan los datos correspondientes.

- **config.py**: Este archivo configura la aplicación Flask, definiendo las rutas y la lógica de la aplicación web. Aquí se encuentran las rutas para la interfaz de usuario, donde los usuarios pueden insertar datos, mostrar información de las temperaturas, realizar búsquedas de fronteras entre países, y obtener las temperaturas a través de las APIs externas. También se gestionan las respuestas a las solicitudes del usuario en este archivo.


## Configuración de la Base de Datos

El proyecto utiliza MySQL como base de datos. Para conectar correctamente a la aplicación, se debe configurar la base de datos tanto en el archivo de configuración de la aplicación (config.py) como en el archivo de configuración de MySQL Workbench (workbench).
se debe solo modificar el user y el passwd con el que estas conectado a tu base de datos local.

## Funcionalidades

La aplicación tiene varias rutas disponibles, que estas rutas estan configuradas para los archivos de html de la carpeta templates:

1. **/ (Página Principal)**: La página principal será el index.html donde la aplicación tendrá enlaces a las demás funcionalidades.
2. **/insertar (Insertar Datos)**: Una página donde puedes insertar los datos de países, fronteras y temperaturas en un botón todos a la vez, y nos mostrará un mensaje si la operación se realizó correctamente.
3. **/mostrar (Mostrar Datos)**: Muestra las temperaturas obtenidas y almacenadas en la base de datos.
4. **/obtener_temperaturas (Obtener Temperaturas)**: Obtiene las temperaturas actuales de los países de Europa desde una API externa y las almacena en la base de datos.
5. **/busqueda (Buscar Fronteras)**: Permite buscar un país y ver su información climática y las fronteras con sus respectivas temperaturas.


## Dependencias

Este proyecto ya tiene las siguientes dependencias en el HTML:
- **Tailwind**: Framework para dar estilos a la aplicación.
- **Alpine**:Framework para dar interacción a la aplicación

Este proyecto requiere las siguientes dependencias para Python:

- **Flask**: Framework web para la aplicación.
- **mysql-connector-python**: Para interactuar con la base de datos MySQL.
- **requests**: Para realizar solicitudes HTTP hacia las APIs externas.

## Errores Conocidos

Este proyecto tiene dos problemas conocidos que pueden afectar la experiencia del usuario:

1. **Duplicación de Países en la Base de Datos**:
    - Si intentamos insertar los mismos datos varias veces, es posible que algunos países se inserten de nuevo en la base de datos. Esto ocurre porque la lógica de inserción no verifica si los datos ya existen antes de insertarlos. Como resultado, puede haber duplicados, lo que podría generar problemas cuando se intente buscar un país.
    - Al buscar el país, puede aparecer duplicado múltiples veces, lo que genera un error de visualización y una experiencia confusa para el usuario.

    **Solución**:
    - Se recomienda verificar la base de datos antes de insertar nuevos países para evitar duplicados. Esta funcionalidad se corregirá en futuras actualizaciones del proyecto.

2. **Problema con la API para "St. Peter Port"**:
    - Actualmente, la API utilizada para obtener las temperaturas de los países no puede recuperar los datos climáticos para "St. Peter Port". Esto ocurre porque el nombre de la ciudad no es reconocido por la API de OpenWeatherMap, lo que puede generar un error o resultados incompletos al intentar obtener la temperatura.

## Ejecucion del Entorno y la Aplicacion de Flask

Se hara estos pasos despues de haber instalado las dependencias:

- **Activar el entorno virtual**:
        .\env\Scripts\activate

- **Ejecutar la aplicación Flask**:
    flask --app config --debug run

En caso que le salgo un error llamado unquote se debe ejecutar este codiog:
    pip install --upgrade flask werkzeug


Puedes instalar estas dependencias ejecutando:

```bash
pip install -r requirements.txt



