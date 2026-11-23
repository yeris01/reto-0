from app import app

cliente = app.test_client()


def test_pagina_principal_responde():
    respuesta = cliente.get("/", follow_redirects=True)
    assert respuesta.status_code == 200
