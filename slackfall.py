#!/usr/bin/env python

import json, sys, os, logging
from flask import Flask, jsonify, request, render_template
from game import Game

VERSION = '0.1'
CONFIGURATION = {}

app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

@app.route("/", methods=['GET'])
def index():
	return "Nothing to see here, move along please!"

@app.route("/instructions", methods=['GET'])
def instructions():
	return render_template('instructions.html', locations=sorted(game.get_locations()))

@app.route("/slcb", methods=['POST'])
def slack_callback():
	""" Commands will be sent here. Validate the source then pass to the game engine for processing. """
	if request.form['token'] != CONFIGURATION['incoming_token']:
		return jsonify({})
	if request.form['user_name'] == 'slackbot':
		return jsonify({})
	if request.form['text'][0] != '!':
		logger.error('Unexpected prefix: [%s]' % request.form['text'])
		return jsonify({})
	message = {
		'sender': request.form['user_name'],
		'text': request.form['text']
	}

	res = False
	bits = request.form['text'][1:].split()
	if len(bits) > 0:
		message['command'] = bits[0]
		message['args'] = bits[1:]
		res = game.handle_message(message)
	if not res:
		return jsonify({})
	return jsonify(text=res)

if __name__ == "__main__":
	configuration_file = 'config.json'
	if len(sys.argv) == 2:
		configuration_file = sys.argv[1]

	if not os.path.isfile(configuration_file):
		print 'Configuration file [%s] not found!' % configuration_file
		sys.exit(1)

	with open(configuration_file) as json_file:
		CONFIGURATION = json.load(json_file)

	config_keys = CONFIGURATION.keys()
	for config_option in ['debug','listen','base_url','incoming_token','outgoing_url','channel','locations']:
		if not config_option in config_keys:
			print 'Missing "%s" from the configuration file!' % config_option
			sys.exit(1)
		elif config_option == 'listen':
			if not 'host' in CONFIGURATION['listen'].keys() or not 'port' in CONFIGURATION['listen'].keys():
				print 'Missing listen host or port from the configuration file!' % config_option
				sys.exit(1)

	game = Game(
		version=VERSION,
		debug=CONFIGURATION['debug'],
		base_url=CONFIGURATION['base_url'],
		outgoing_url=CONFIGURATION['outgoing_url'],
		channel=CONFIGURATION['channel'],
		locations=CONFIGURATION['locations']
	)

	app.run(
		host=CONFIGURATION['listen']['host'],
		port=int(CONFIGURATION['listen']['port']),
		debug=CONFIGURATION['debug']
	)
