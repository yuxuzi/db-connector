import unittest
from typer.testing import CliRunner
from db_connector.cli import app

runner = CliRunner()

class TestCLI(unittest.TestCase):
    def test_set_credentials_help(self):
        result = runner.invoke(app, ["set-credentials", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Usage", result.output)

    def test_check_credentials_help(self):
        result = runner.invoke(app, ["check-credentials", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Usage", result.output)

    def test_get_engine_help(self):
        result = runner.invoke(app, ["get-engine", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Usage", result.output)

if __name__ == '__main__':
    unittest.main()
