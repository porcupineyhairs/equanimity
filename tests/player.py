from base import FlaskTestDB
from equanimity.player import Player, WorldPlayer
from equanimity.const import WORLD_UID


class PlayerTest(FlaskTestDB):

    def test_get_player_bad_uid(self):
        player = Player.get('xxx')
        self.assertIs(player, None)

    def test_is_world(self):
        player = Player('x', 'x', 'x')
        self.assertFalse(player.is_world())

    def test_repr(self):
        player = Player('x', 'x', 'x')
        self.assertEqual(str(player), '<Player: 1>')


class WorldPlayerTest(FlaskTestDB):

    def test_create(self):
        player = WorldPlayer()
        self.assertEqual(player.uid, WORLD_UID)

    def test_is_world(self):
        player = WorldPlayer()
        self.assertTrue(player.is_world())

    def test_persist(self):
        player = WorldPlayer()
        player.persist()
        self.assertTrue(self.db['players'][0])
        self.assertEqual(self.db['players'][0].uid, player.uid)
