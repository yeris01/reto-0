# AGENTS.md

## Proyecto
Aplicación web privada para gestionar una agenda de contactos con registro e inicio de sesión.
Permite crear, buscar, editar, eliminar y exportar contactos a CSV.

## Stack
- Framework: Flask 3; Python.
- Base de datos: SQLite mediante sqlite3.
- Librerías principales: python-dotenv, Jinja2, Werkzeug.

## Comandos
- Instalar: `python -m venv .venv`, activar el entorno y `pip install -r requirements.txt`
- Ejecutar: `python app.py`
- Pruebas: `python -m pytest -v`
- Estilo: `ruff check .`

## Estructura
- `app.py`: fábrica Flask, rutas, sesiones, CSRF, usuarios, contactos y exportación CSV.
- `static/`: recursos estáticos; `static/style.css` contiene el diseño responsive.
- `templates/`: vistas Jinja2; `base.html`, `index.html`, `contact_form.html`, `login.html` y `register.html`.
- `tests/`: pruebas automatizadas; `tests/test_app.py` cubre registro, privacidad, CSV y CSRF.
- `instance/`: archivos de ejecución; `instance/contacts.sqlite3` guarda la base principal.
- `.env`: configuración local de entorno; no debe contener valores compartidos.
- `.env.example`: plantilla de variables de entorno.
- `requirements.txt`: dependencias de Flask y python-dotenv.
- `README.md`: documentación de requisitos, ejecución y pruebas legacy.
- `.gitignore`: excluye entornos, secretos, bases locales y cachés.
- `.venv/`: entorno virtual local ya creado.

## Qué no hacer
- No modificar las pruebas para que pasen.
- No escribir claves en el código.
- No instalar dependencias sin explicar para qué.
- No hacer commit ni push.

## Lecciones aprendidas
