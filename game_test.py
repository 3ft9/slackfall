import unittest
from game import Game

class GameTestCase(unittest.TestCase):
	def setUp(self):
		self.TEST_VERSION = '0.1'
		self.TEST_DEBUG = False
		self.TEST_BASE_URL = 'http://127.0.0.1:1001/'
		self.TEST_OUTGOING_URL = 'http://127.0.0.1:1002/'
		self.TEST_CHANNEL = '#slackfall'
		self.TEST_LOCATIONS = {'home': {'name': 'Home', 'roles': ['Mother','Father','Son','Daughter','Baby','Cat','Dog']}}

		self.game = Game(
			self.TEST_VERSION,
			self.TEST_DEBUG,
			self.TEST_BASE_URL,
			self.TEST_OUTGOING_URL,
			self.TEST_CHANNEL,
			self.TEST_LOCATIONS
		)

	def tearDown(self):
		self.game = None
       
	def test_initial_state(self):
		""" Check the initial state """
		self.assertEqual(self.game._version, self.TEST_VERSION, '_version is incorrect')
		self.assertEqual(self.game._debug, self.TEST_DEBUG, '_debug is incorrect')
		self.assertEqual(self.game._base_url, self.TEST_BASE_URL, '_base_url is incorrect')
		self.assertEqual(self.game._outgoing_url, self.TEST_OUTGOING_URL, '_outgoing_url is incorrect')
		self.assertEqual(self.game._channel, self.TEST_CHANNEL, '_channel is incorrect')
		self.assertEqual(self.game._locations, self.TEST_LOCATIONS, '_locations is incorrect')
		self.assertEqual(self.game._state, 'none', '_state is incorrect')
		self.assertEqual(self.game._dealer, '', '_dealer is incorrect')
		self.assertEqual(self.game._game_duration, 0, '_game_duration is incorrect')
		self.assertEqual(self.game._end_time, 0, '_end_time is incorrect')
		self.assertEqual(self.game._paused_at, 0, '_paused_at is incorrect')
		self.assertEqual(self.game._last_time_displayed, 0, '_last_time_displayed is incorrect')
		self.assertEqual(self.game._current_spy, '', '_current_spy is incorrect')
		self.assertEqual(self.game._current_location, '', '_current_location is incorrect')
		self.assertEqual(self.game._players, {}, '_players is incorrect')
		self.assertEqual(self.game._called_vote, [], '_called_vote is incorrect')
		self.assertEqual(self.game._accused, '', '_accused is incorrect')
		self.assertEqual(self.game._votes, [], '_votes is incorrect')
		self.assertEqual(self.game._abandon_count, 0, '_abandon_count is incorrect')

	def test_init_command(self):
		""" Initialise a 5 minute game """
		res = self.game.handle_message({'sender':'user1', 'text':'!init', 'command':'init', 'args':['5']})

		self.assertEqual(res, 'Game initialised. @user1 has joined the game. Current players: @user1. A minimum of 4 players is required to start a game!', 'init command failed')
		self.assertEqual(self.game._dealer, 'user1', 'Dealer is incorrect')
		self.assertEqual(self.game._players, {'user1':'unknown'}, 'Players dict is incorrect')
		self.assertEqual(self.game._state, 'initialised', 'game state is incorrect')
		
		""" Reset the game and check the state """
		self.game.reset()
		self.test_initial_state()
	
	def test_join_command(self):
		""" Join an initialised game 9 times and check the responses at every step """
		
		""" Initialise the game """
		self.game.handle_message({'sender':'user1', 'text':'!init', 'command':'init', 'args':['5']})
		
		""" Add player 2 """
		res = self.game.handle_message({'sender':'user2', 'text':'!join', 'command':'join', 'args':[]})
		self.assertEqual(res, '@user2 has joined the game. Current players: @user1, @user2. A minimum of 4 players is required to start a game!')
		self.assertEqual(self.game._dealer, 'user1', 'Dealer is incorrect')
		self.assertEqual(self.game._players, {'user2':'unknown','user1':'unknown'}, 'Players dict is incorrect')
		self.assertEqual(self.game._state, 'initialised', 'game state is incorrect')
		
		""" Attempt to add player 1 again """
		res = self.game.handle_message({'sender':'user1', 'text':'!join', 'command':'join', 'args':[]})
		self.assertEqual(res, '@user1 has joined the game. Current players: @user1, @user2. A minimum of 4 players is required to start a game!')
		self.assertEqual(self.game._dealer, 'user1', 'Dealer is incorrect')
		self.assertEqual(self.game._players, {'user2':'unknown','user1':'unknown'}, 'Players dict is incorrect')
		self.assertEqual(self.game._state, 'initialised', 'game state is incorrect')
		
		""" Add player 3 """
		res = self.game.handle_message({'sender':'user3', 'text':'!join', 'command':'join', 'args':[]})
		self.assertEqual(res, '@user3 has joined the game. Current players: @user1, @user2, @user3. A minimum of 4 players is required to start a game!')
		self.assertEqual(self.game._dealer, 'user1', 'Dealer is incorrect')
		self.assertEqual(self.game._players, {'user2':'unknown','user1':'unknown','user3':'unknown'}, 'Players dict is incorrect')
		self.assertEqual(self.game._state, 'initialised', 'game state is incorrect')
		
		""" Add player 4 """
		res = self.game.handle_message({'sender':'user4', 'text':'!join', 'command':'join', 'args':[]})
		self.assertEqual(res, '@user4 has joined the game. Current players: @user1, @user2, @user3, @user4. The game can be started by @user1 issuing the !start command.')
		self.assertEqual(self.game._dealer, 'user1', 'Dealer is incorrect')
		self.assertEqual(self.game._players, {'user2':'unknown','user1':'unknown','user3':'unknown','user4':'unknown'}, 'Players dict is incorrect')
		self.assertEqual(self.game._state, 'initialised', 'game state is incorrect')
		
		""" Add player 5 """
		res = self.game.handle_message({'sender':'user5', 'text':'!join', 'command':'join', 'args':[]})
		self.assertEqual(res, '@user5 has joined the game. Current players: @user1, @user2, @user3, @user4, @user5. The game can be started by @user1 issuing the !start command.')
		self.assertEqual(self.game._dealer, 'user1', 'Dealer is incorrect')
		self.assertEqual(self.game._players, {'user5':'unknown','user2':'unknown','user1':'unknown','user3':'unknown','user4':'unknown'}, 'Players dict is incorrect')
		self.assertEqual(self.game._state, 'initialised', 'game state is incorrect')
		
		""" Add player 6 """
		res = self.game.handle_message({'sender':'user6', 'text':'!join', 'command':'join', 'args':[]})
		self.assertEqual(res, '@user6 has joined the game. Current players: @user1, @user2, @user3, @user4, @user5, @user6. The game can be started by @user1 issuing the !start command.')
		self.assertEqual(self.game._dealer, 'user1', 'Dealer is incorrect')
		self.assertEqual(self.game._players, {'user5':'unknown','user6':'unknown','user2':'unknown','user1':'unknown','user3':'unknown','user4':'unknown'}, 'Players dict is incorrect')
		self.assertEqual(self.game._state, 'initialised', 'game state is incorrect')
		
		""" Add player 7 """
		res = self.game.handle_message({'sender':'user7', 'text':'!join', 'command':'join', 'args':[]})
		self.assertEqual(res, '@user7 has joined the game. Current players: @user1, @user2, @user3, @user4, @user5, @user6, @user7. The game can be started by @user1 issuing the !start command.')
		self.assertEqual(self.game._dealer, 'user1', 'Dealer is incorrect')
		self.assertEqual(self.game._players, {'user5':'unknown','user6':'unknown','user2':'unknown','user1':'unknown','user3':'unknown','user4':'unknown','user7':'unknown'}, 'Players dict is incorrect')
		self.assertEqual(self.game._state, 'initialised', 'game state is incorrect')
		
		""" Add player 8 """
		res = self.game.handle_message({'sender':'user8', 'text':'!join', 'command':'join', 'args':[]})
		self.assertEqual(res, '@user8 has joined the game. Current players: @user1, @user2, @user3, @user4, @user5, @user6, @user7, @user8. This is the maximum number of players. The game can be started by @user1 issuing the !start command.')
		self.assertEqual(self.game._dealer, 'user1', 'Dealer is incorrect')
		self.assertEqual(self.game._players, {'user5':'unknown','user6':'unknown','user2':'unknown','user8':'unknown','user1':'unknown','user3':'unknown','user4':'unknown','user7':'unknown'}, 'Players dict is incorrect')
		self.assertEqual(self.game._state, 'initialised', 'game state is incorrect')
		
		""" Attempt to add a 9th player """
		res = self.game.handle_message({'sender':'user9', 'text':'!join', 'command':'join', 'args':[]})
		self.assertEqual(res, 'No more players can be added; 8 is the maximum. The game can be started by @user1 issuing the !start command.')
		self.assertEqual(self.game._dealer, 'user1', 'Dealer is incorrect')
		self.assertEqual(self.game._players, {'user5':'unknown','user6':'unknown','user2':'unknown','user8':'unknown','user1':'unknown','user3':'unknown','user4':'unknown','user7':'unknown'}, 'Players dict is incorrect')
		self.assertEqual(self.game._state, 'initialised', 'game state is incorrect')
		

	def test_init_after_init_and_join(self):
		""" Reinitialise a game after initialising and adding another user """

		""" Initialise the game """
		self.game.handle_message({'sender':'user1', 'text':'!init', 'command':'init', 'args':['5']})
		
		""" Add player 2 """
		self.game.handle_message({'sender':'user2', 'text':'!join', 'command':'join', 'args':[]})
		
		""" Attempt to initialise the game again """
		res = self.game.handle_message({'sender':'user1', 'text':'!init', 'command':'init', 'args':['10']})
		self.assertEquals(res, 'Game reinitialised. @user1 has joined the game. Current players: @user1, @user2. A minimum of 4 players is required to start a game!')

	def test_leave_command(self):
		""" Initialise a game, add another user, then that user leaves """
		
		""" Initialise the game """
		self.game.handle_message({'sender':'user1', 'text':'!init', 'command':'init', 'args':['5']})
		
		""" Add player 2 """
		self.game.handle_message({'sender':'user2', 'text':'!join', 'command':'join', 'args':[]})
		
		""" Remove player 2 """
		res = self.game.handle_message({'sender':'user2', 'text':'!leave', 'command':'leave', 'args':[]})
		self.assertEquals(res, '@user2 has left the game. Current players: @user1. A minimum of 4 players is required to start a game!')
		
		""" Attempt to remove player 1 (the dealer) """
		res = self.game.handle_message({'sender':'user1', 'text':'!leave', 'command':'leave', 'args':[]})
		self.assertEquals(res, 'You are the dealer so you cannot simply leave the game. If you want to leave you must use the !abandon command instead.')
		
		""" Attempt to remove a player that hasn't been added """
		res = self.game.handle_message({'sender':'user3', 'text':'!leave', 'command':'leave', 'args':[]})
		self.assertEquals(res, '@user3 is not in the players list!')
