import csv
import io
import sqlite3
import tempfile
import unittest
from contextlib import closing

from app import create_app


class ContactAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.temp_dir.name + "/test.sqlite3",
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def post_form(self, url, data):
        self.client.get("/login")
        with self.client.session_transaction() as session:
            token = session["csrf_token"]
        return self.client.post(url, data=dict(data, csrf_token=token), follow_redirects=True)

    def register(self, username="ana"):
        return self.post_form("/register", {"username": username, "password": "secure-pass-123"})

    def test_registration_contact_search_and_csv_export(self):
        response = self.register()
        self.assertEqual(response.status_code, 200)

        response = self.post_form("/contacts/new", {
            "name": "Ana Pérez", "email": "ana@example.com", "phone": "555-0101", "notes": ""
        })
        self.assertIn("Contacto guardado", response.get_data(as_text=True))
        self.assertIn("Ana Pérez", self.client.get("/?q=Ana").get_data(as_text=True))
        self.assertNotIn("Ana Pérez", self.client.get("/?q=Luis").get_data(as_text=True))

        exported = self.client.get("/export")
        self.assertEqual(exported.status_code, 200)
        self.assertIn("text/csv", exported.content_type)
        rows = list(csv.reader(io.StringIO(exported.get_data(as_text=True).lstrip("\ufeff"))))
        self.assertEqual(rows[1], ["Ana Pérez", "ana@example.com", "555-0101", ""])

    def test_users_cannot_access_another_users_contact(self):
        self.register("ana")
        self.post_form("/contacts/new", {"name": "Privado", "email": "", "phone": "", "notes": ""})
        with closing(sqlite3.connect(self.temp_dir.name + "/test.sqlite3")) as db:
            contact_id = db.execute("SELECT id FROM contacts").fetchone()[0]

        self.post_form("/logout", {})
        self.register("luis")
        self.assertEqual(self.client.get("/contacts/{}/edit".format(contact_id)).status_code, 404)
        self.assertNotIn("Privado", self.client.get("/export").get_data(as_text=True))

    def test_csv_neutralizes_spreadsheet_formulas(self):
        self.register()
        self.post_form("/contacts/new", {"name": "=1+1", "email": "", "phone": "", "notes": ""})
        response = self.client.get("/export")
        rows = list(csv.reader(io.StringIO(response.get_data(as_text=True).lstrip("\ufeff"))))
        self.assertEqual(rows[1][0], "'=1+1")

    def test_post_requires_csrf_token(self):
        response = self.client.post("/register", data={"username": "ana", "password": "secure-pass-123"})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
