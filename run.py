import os
from dotenv import load_dotenv
# Importamos la FUNCIÓN create_app desde el PAQUETE optica_app
from optica_app import create_app 

# Cargar variables del .env
load_dotenv()

# Ejecutamos la función para obtener la instancia de Flask
app = create_app()

if __name__ == '__main__':
    # Ahora 'app' es una instancia de Flask y tiene el método .run()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)