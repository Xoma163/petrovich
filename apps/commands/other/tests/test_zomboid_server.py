from django.test import SimpleTestCase

from apps.connectors.parsers.zomboid.zomboid_server import ZomboidServer


class ZomboidServerTest(SimpleTestCase):
    def test_parse_players_with_player_names(self):
        data = ZomboidServer.parse_players("Players connected (2):\n-AndrewSha\n-Petrovich")

        self.assertEqual(data.players_online, 2)
        self.assertEqual(data.players, ["AndrewSha", "Petrovich"])

    def test_parse_players_without_players(self):
        data = ZomboidServer.parse_players("Players connected (0):")

        self.assertEqual(data.players_online, 0)
        self.assertEqual(data.players, [])

    def test_parse_players_strips_ansi_service_output(self):
        output = (
            "\x1b[1m\n"
            "\x1b[K[\x1b[32m  OK   \x1b[0m] \x1b[0m Send pzserver: Sending command to console: \"players\" \x1b[0m"
        )

        data = ZomboidServer.parse_players(output)

        self.assertIsNone(data.players_online)
        self.assertNotIn("\x1b", data.raw_status)
