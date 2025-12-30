import unittest
from flask import Flask
from app.routes import bp
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        template_dir = BASE_DIR.parent / "app" / "templates"
        self.app = Flask(__name__, template_folder=str(template_dir))
        self.app.register_blueprint(bp)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_index_get(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(b"form_data" in resp.data or b"<form" in resp.data)

    def test_index_post(self):
        resp = self.client.post("/", data={"foo": "bar"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(b"form_data" in resp.data or b"<form" in resp.data)

    def test_simulate_route_exists(self):
        resp = self.client.post("/simulate", data={})
        self.assertIn(resp.status_code, (200, 400))

    def test_simulate_minimal_valid(self):
        data = {
            "loan_amount_0": "1000",
            "apr_0": "5",
            "term_months_0": "12",
            "monthly_budget": "100",
            "years": "1",
        }
        resp = self.client.post("/simulate", data=data)
        self.assertEqual(resp.status_code, 200)
        # Check for the Results heading in the rendered HTML
        self.assertIn(b'<h2 style="margin-bottom:1.2rem">Results (', resp.data)
