import json, urllib2, threading, time, math, logging
from enum import enum
from flask import jsonify, request
from randomdotorg import RandomDotOrg
random = RandomDotOrg('SlackFall')

"""
Game states:
	none
	initialised
	dealt
	running
	voting
"""

class Game:
	def __init__(self, version, debug, base_url, outgoing_url, channel, locations):
		self._version = version
		self._debug = debug
		self._base_url = base_url
		self._outgoing_url = outgoing_url
		self._channel = channel
		self._locations = locations
		self.reset()
		self.send_to_slack(self._channel, "The bot has been restarted.")

	def send_to_slack(self, dest, message):
		try:
			req = urllib2.Request(self._outgoing_url)
			req.add_header('Content-Type', 'application/json; charset=utf-8')
			req.add_header('User-Agent', 'SlackFall/' + self._version)
			data = json.dumps({'channel': dest, 'text': message})
			response = urllib2.urlopen(req, data)
			if response.code != 200:
				logging.error("HTTP error: %s" % err.read())
				return False
			return True
		except urllib2.HTTPError as err:
			logging.error("HTTP error: %s" % err.read())
			return False

	def reset(self):
		self._state = 'none'
		self._dealer = ''
		self._game_duration = 0
		self._end_time = 0
		self._paused_at = 0
		self._last_time_displayed = 0
		self._current_spy = ''
		self._current_location = ''
		self._players = {}
		self._called_vote = []
		self._accused = ''
		self._votes = []
		self._abandon_count = 0
	
	def get_locations(self):
		retval = []
		for location in self._locations.keys():
			retval.append(self._locations[location]['name'])
		return retval
	
	def game_dealt(self):
		return self._state in ['dealt', 'running', 'voting']
		
	def game_initialised(self):
		return self._state in ['initialised']

	def game_running(self):
		return self._state in ['running', 'voting']

	def game_paused(self):
		return self._state in ['voting']

	def handle_message(self, message):
		if self.game_running() and not message['sender'] in self._players.keys():
			return False
		fn = "%s_cmd" % message['command']
		if hasattr(self, fn):
			if message['command'] != 'abandon':
				self._abandon_count = 0
			return getattr(self, fn)(message)
		return False

	def display_time_left(self):
		if not self.game_running():
			logging.info("display_time_left: Game is not running!")
		elif self.game_paused():
			logging.info("display_time_left: Game is paused")
		elif self._end_time < time.time():
			self.game_timed_out()
		else:
			secs_left = self._end_time - time.time()
			mins_left = int(math.floor(secs_left / 60))
			secs_left = int(math.floor(secs_left - (mins_left * 60)))
			
			display = False
			if mins_left > 0 and secs_left == 0:
				if mins_left > 5 and mins_left % 5 == 0:
					display = True
				else:
					display = True
					if mins_left == 1:
						time_left = '1 minute'
					else:
						time_left = '%d minutes' % mins_left
			elif mins_left == 0:
				if secs_left == 30:
					display = True
					time_left = '30 seconds'
				elif secs_left == 15:
					display = True
					time_left = '15 seconds'
				elif secs_left == 5:
					display = True
					time_left = '5 seconds'

			if display:
				self.send_to_slack(self._channel, "The timer is running: %s to go." % time_left)
				self._last_time_displayed = time_left

			threading.Timer(0.5, self.display_time_left).start()

	def game_timed_out(self):
		self.send_to_slack(self._channel, "Time's up! The spy was... @%s, and the location was... %s!" % (self._current_spy, self._locations[self._current_location]['name']))
			
		self.reset()
	
	def game_ends_with_accusation(self):
		message = "Everyone has agreed with the accusation that @%s is the spy. The spy was... @%s!" % (self._accused, self._current_spy)
		if self._accused == self._current_spy:
			message = "%s Congratulations!" % message
		else:
			message = "%s You all suck, the spy wins!" % message
		message = "%s For they spy's information, the location was... %s." % (message, self._locations[self._current_location]['name'])
		self.reset()
		return message
		
	def game_ends_with_spy_guess(self, guess):
		if guess != self._current_location:
			if not guess in self._locations.keys():
				return "Unknown location. You've now outed yourself as the spy, so you might as well <" + self._base_url + "/instructions|check the spelling> and try again in case you were right!"
			else:
				message = "Incorrect. The correct location was... %s. Well done to the rest of you!" % self._locations[self._current_location]['name']
		else:
			message = "Correct, the location was... %s. Congratulations, Sir Spy!" % self._locations[self._current_location]['name']
		self.reset()
		return message

	def init_cmd(self, message):
		if self.game_running():
			return "There's already a game in progress. " + self._dealer + " can abandon the game with the abandon command."
		
		reinit = self._state == 'initialised'

		if len(message['args']) != 1:
			return "Please specify the game length in minutes."

		players = {}
		if reinit:
			players = self._players
		self.reset()
		self._players = players
	
		self._dealer = message['sender']
		
		self._game_duration = int(message['args'][0])
		if self._game_duration <= 0:
			self.reset()
			return "Invalid game duration!"
		self._game_duration = self._game_duration * 60

		if reinit:
			res = "Game reinitialised."
		else:
			res = "Game initialised."		
		self._state = 'initialised'
		res = "%s %s" % (res, self.join_cmd(message))
		return res
	
	def join_cmd(self, message):
		if self.game_running():
			return "There's already a game in progress. @%s can abandon the game with the abandon command." % self._dealer
		if self.game_dealt():
			return "The game has already been dealt. @%s can reset the game by issuing the !reset command." % self._dealer
		if not self.game_initialised():
			return "The game needs to be initialised with the !init command before you can join it!"
		if not message['sender'] in self._players.keys():
			if len(self._players.keys()) >= 8:
				return "No more players can be added; 8 is the maximum. The game can be started by @%s issuing the !start command." % self._dealer
			self._players[message['sender']] = 'unknown'
		res = '@%s has joined the game. Current players: @%s.' % (message['sender'], ', @'.join(sorted(self._players.keys())))
		if len(self._players.keys()) == 8:
			res = "%s This is the maximum number of players." % res
		if len(self._players.keys()) >= 4:
			res = "%s The game can be started by @%s issuing the !start command." % (res, self._dealer)
		else:
			res = "%s A minimum of 4 players is required to start a game!" % res
		return res
	
	def leave_cmd(self, message):
		if self.game_running():
			return "There's already a game in progress. @%s can abandon the game with the abandon command." % self._dealer
		if self.game_dealt():
			return "The game has already been dealt. @%s can reset the game by issuing the !reset command." % self._dealer
		if not self.game_initialised():
			return "The game needs to be initialised with the !init command before you can leave it!"
		if not message['sender'] in self._players.keys():
			return "@%s is not in the players list!" % message['sender']
		if message['sender'] == self._dealer:
			return "You are the dealer so you cannot simply leave the game. If you want to leave you must use the !abandon command instead."
		del self._players[message['sender']]
		res = '@%s has left the game. Current players: @%s.' % (message['sender'], ', @'.join(sorted(self._players.keys())))
		if len(self._players.keys()) == 8:
			res = "%s This is the maximum number of players." % res
		if len(self._players.keys()) >= 4:
			res = "%s The game can be started by @%s issuing the !start command." % (res, self._dealer)
		else:
			res = "%s A minimum of 4 players is required to start a game!" % res
		return res
	
	def deal_cmd(self, args):
		if self.game_running():
			return "There's already a game in progress. " + self._dealer + " can abandon the game with the abandon command."

		if not len(self._players.keys()) in range(4,8):
			return "Invalid number of players; at least 4 and no more than 8 players are required. Current player list is @%s." % ', @'.join(self._players.keys())

		self._current_spy = random.choice(self._players.keys())
		self._players[self._current_spy] = 'spy'
		
		self._current_location = random.choice(self._locations.keys())
		
		for player in self._players.keys():
			if player != self._current_spy:
				role = ''
				while role == '' or role in self._players.values():
					role = random.choice(self._locations[self._current_location]['roles'])
				self._players[player] = role
		
		for player in self._players.keys():
			if self._players[player] == 'spy':
				message = 'You are the spy! Use the guess command when you think you know the location.'
			else:
				message = 'The location is "%s", and your role is "%s." Use the accuse command when you think you know who\'s spying!' % (self._locations[self._current_location]['name'], self._players[player])
			if not self.send_to_slack('@%s' % player, message):
				self.reset()
				return "Failed to start game: could not send a private message to @%s!" % player

	 	self._state = 'dealt'
		return "The game is dealt. @%s can now start the game with the start command." % self._dealer

	def start_cmd(self, message):
		if not self.game_dealt():
			return "No game has been dealt yet. Why not start one?"
		if message['sender'] != self._dealer:
			return False
		self._end_time = time.time() + self._game_duration + 1
		self.display_time_left()
		self._state = 'running'
		return self.locations_cmd(message)

	def abandon_cmd(self, message):
		if not self.game_running():
			if self.game_dealt():
				return "The game has been dealt but not started. You can deal again with the deal command."
			else:
				if self.game_initialised():
					if message['sender'] != self._dealer:
						return "You cannot abandon this game, but you can reinitialise it with the !init command."
				else:
					return "There is no game happening. Why not start one?"
		if message['sender'] != self._dealer:
			return "Only @%s can use this command!" % self._dealer
	
		if self._abandon_count == 0:
			self._abandon_count = 1
			return "Send the !abandon command again to confirm that you want to abandon the current game."
		
		self.reset()
		return "The game has been abandoned by the dealer. Why not start a new game?"

	def accuse_cmd(self, message):
		if not self.game_running():
			return False
		if self.game_paused():
			return "An accusation vote is already in progress!"
		if len(message['args']) == 0:
			return "Please tell me who you are accusing..."
		if not message['args'][0] in self._players.keys():
			return "I don't have @%s in the player list. Are you sure that's who you meant?" % args[0]
		if message['args'][0] == message['sender']:
			return "I don't feel right allowing you to accuse yourself!"
		if message['sender'] in self._called_vote:
			return "You have already called a vote during this game!"

		self._paused_at = time.time()
		self._called_vote.append(message['sender'])
		self._accused = args[0]
		self._votes = []
		for player in self._players.keys():
			if player != self._accused and player != message['sender']:
				self._votes.append(player)

		secs_left = self._end_time - time.time()
		mins_left = int(math.floor(secs_left / 60))
		secs_left = int(math.floor(secs_left - (mins_left * 60)))
		prefix = ''
		if secs_left < 10:
			prefix = '0'
		time_left = "%d:%s%d" % (mins_left, prefix, secs_left)
		
		self._state = 'voting'

		return "@here: @%s has accused @%s of being the spy. The timer is paused with %s to go. To agree say 'yes', otherwise say 'no'. The first 'no' vote will restart the timer. Waiting for votes from %s..." % (message['sender'], self._accused, time_left, ', '.join(self._votes))
	
	def yes_cmd(self, message):
		if not self.game_paused():
			return False
		if message['sender'] in self._votes:
			self._votes.remove(message['sender'])
		if len(self._votes) == 0:
			return self.game_ends_with_accusation()
		return "Still waiting for %s..." % ', '.join(self._votes)
	
	def no_cmd(self, message):
		if not self.game_paused():
			return False
		if not message['sender'] in self._votes:
			return False
		self._end_time += (time.time() - self._paused_at)
		self._paused_at = 0

		secs_left = self._end_time - time.time()
		mins_left = int(math.floor(secs_left / 60))
		secs_left = int(math.floor(secs_left - (mins_left * 60)))
		prefix = ''
		if secs_left < 10:
			prefix = '0'
		time_left = "%d:%s%d" % (mins_left, prefix, secs_left)
		
		self.display_time_left()
		
		return "Vote failed. The timer has been resumed with %s to go." % time_left
	
	def locations_cmd(self, message):
		return "Locations: [%s]" % "] [".join(sorted(self.get_locations()))
	
	def guess_cmd(self, message):
		if not self.game_running() or self.game_paused():
			return False
		self._abandon_count = 0
		if request.form['user_name'] != self._current_spy:
			return ""
		if len(args) == 0:
			return "Please state which location you think it is..."
		return self.game_ends_with_spy_guess(' '.join(args).lower())

	def help_cmd(self, message):
		return "See the <%s/instructions|SlackFall Instructions> for help." % self._base_url
