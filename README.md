# Agenda de contactos

Aplicación web en Python para guardar contactos privados, buscarlos por nombre e importarlos en una hoja de cálculo mediante CSV.

## Requisitos

- Python 3.10 o posterior
- pip

## Ejecutar localmente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
python app.py
```

Abre http://127.0.0.1:5000, crea una cuenta y añade contactos. Para conservar sesiones al reiniciar, define `SECRET_KEY` con un valor persistente y privado. La base SQLite se crea automáticamente en `instance/contacts.sqlite3`.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```
