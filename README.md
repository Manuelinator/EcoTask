🛠 En desarrollo

Esto es una página para tratar de fomentar el reciclaje mediante objetivos diarios.

Requiere de estas dependencias:

flask  
    
flask_sqlalchemy  
    
flask_login
    
werkzeug  
    
apscheduler  
    
pillow  
    
numpy  
    
tensorflow 

keras  


Idealmente todo esto iría metido en un entorno virtual, pero es opcional.

La estructura del proyecto es la siguiente:

    EcoTasks/
    │
    ├── app/
    │   └── keras_model/               # Modelo de TensorFlow (SavedModel)
    │
    ├── static/
    │   └── profile_pics/              # Fotos de perfil de los usuarios
    │
    ├── templates/
    │   ├── home.html
    │   ├── registrarse.html
    │   └── iniciar_sesion.html
    │
    ├── db.sqlite3                     # Base de datos SQLite 
    ├── main.py                        # Código principal de la aplicación Flask
    └── README.md


Características principales

    Registro e inicio de sesión de usuarios con foto de perfil.

    Asignación automática de desafíos diarios.

    Subida de imágenes para identificar residuos con IA.

    Seguimiento del progreso y cantidad de residuos reciclados.

    Reinicio automático de retos cada 24 horas.

Notas importantes

    El modelo de IA debe estar exportado en formato SavedModel (app/keras_model).

    Si quieres restablecer los usuarios o los desafíos, borra el archivo db.sqlite3.

    Actualmente la aplicación está pensada para ejecutarse en una red local. Para uso público, necesitarías desplegarla en un servidor web (Heroku, PythonAnywhere, etc.).

🛠 En desarrollo
