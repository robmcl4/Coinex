import unittest
import coinex_api


class TestAPIFunctions(unittest.TestCase):

    def set_up(self):
        pass

    def test_config_load(self):
        # do this twice to test memoization
        conf = coinex_api._get_config()
        conf = coinex_api._get_config()

        self.assertTrue('Credentials' in conf, "Config should have credentials")
        self.assertTrue('Key' in conf['Credentials'], "Config should have key")
        self.assertTrue(
            'Secret' in conf['Credentials'],
            "Config should have secret"
        )

if __name__ == '__main__':
    unittest.main()
