# 6/10/2018 And here we go with a Python version

# Re Perl version...
# 11/06/2013 It's finished (well, as much as I'm going to do).
# ie I haven't added any fancy functionality (eg save/load games, allow variable turns). I'll save that for a later version.
# traders_script2.txt & traders_script4.txt play back perfectly :) Well done Andrew! Give yourself a pat on the back!

# F:\code\starlanes\python> cls & python StarLanes.py --script ..\traders_script2.txt

#----------------------------------------------------------------------------
# Star Lanes (also known as Star Traders).
# Python version by Andrew Vander.
# Ported from my Perl version which I ported from a Basic version.
#
# According to http://www.classictw.com/viewtopic.php?f=14&t=11882 ...
# The original door game was written by Chris Sherrick.
# Chris was inspired by a game called Star Traders (aka Star Lanes) that was
# published in a book called The People's Book of Computer Games.
# Modified for 'Altair Basic 4.0' By S J Singer
#----------------------------------------------------------------------------

import argparse
import re
from pprint import pprint as pp
#import parser
import random
import yaml # for comparing
import sys
import os
import inspect
import json # for saving/loading game
#import tkinter as tk
#from tkinter import filedialog
import wx # from command line with admin privs... pip install wxPython

import Script

MARKER_VACANT = ' '
MARKER_OUTPOST = '+'
MARKER_STAR = '*'
MARKER_A = 'A'
MARKER_B = 'B'
MARKER_C = 'C'
MARKER_D = 'D'
MARKER_E = 'E'
MARKER_GROUP_COMPANY = '~'  # will not appear on map. used to represent 'all companies'

MAX_PLAYERS = 4
MAX_ROW = 9
MAX_COL = 12
MAX_LEGAL_MOVES = 5

MAX_SHARE_PRICE = 3000
SHARE_PRICE_STD_INC = 100  # 100 standard share price increment
SHARE_PRICE_START_STAR = 500
SHARE_PRICE_START_NO_STAR = 100

NUM_SHARES_FOUNDER = 5

STARTING_CASH = 6000

TURNS = {
	's': 48,  # The classic number of turns
	'm': 60,
	'l': 72,
}

#COMPANY_NAMES = ['Altair', 'Betelgeuse', 'Capella', 'Denebola', 'Eridani']
COMPANY_NAMES = [
	'Altair Starways',
	'Betelgeuse Ltd',
	'Capella Freight Co',
	'Denebola Shippers',
	'Eridani Expediters',
]

COMPANY_TO_MARKER = {}
MARKER_TO_COMPANY = {}
for cpy in COMPANY_NAMES:
	COMPANY_TO_MARKER[cpy] = cpy[0]
	MARKER_TO_COMPANY[cpy[0]] = cpy

galaxy = []									# part of saved game state
companies = {}  # keyed by company name		# "
player_names = []							# "
players = {}  # keyed by player name		# "
max_turns = 0								# "
turn_num = None								# "
player_turn = None							# "

script_moves = None
script_move = None # taken from script_moves
script_players = None

#----------------------------------------------------------------------------

# So you can code debug msgs like...
# print(str(__LINE__())+' i am here')

class __LINE__(object):

	def __repr__(self):
		try:
			raise Exception
		except:
			return str(sys.exc_info()[2].tb_frame.f_back.f_lineno)

# ----------------------------------------------------------------------------

def play_game():

	print('\nWelcome to Star Lanes!\n')

	while True:
		choice = input('Would you like to load a previously saved game ? ').lower()
		if choice == 'y':
			load_game()
		elif choice == 'n':
			setup_new_game()
		else:
			continue
		break

	global turn_num
	global player_turn
	global script_move

	while turn_num <= max_turns:

		if script_moves:
			script_move = script_moves.pop(0)
			#print('-------------------------------------------------------------')
			print('------------------------------------------------------------- turn_num='+str(turn_num))
			#print __LINE__.": \$script_move = ".Dumper $script_move
			Script.check_map(galaxy, script_move['map_before'])

		#display_score_board()
		#display_map()

		player_turn = player_names[(turn_num - 1) % len(player_names)]

		if script_moves:
			if player_turn != script_move['player']:
				raise Exception('Script error: Actual player "'+player_turn+'" does not match script player "'+script_move['player']+'"')

			if 'scoreboard' in script_move:

				# print __LINE__.": ".Dumper $players[player_turn]['shares'] # die
				print('script_move[\'scoreboard\']:'); pp(script_move['scoreboard'])

				for cpy in sorted(players[player_turn]['shares']):

					if players[player_turn]['shares'][cpy] == 0:
						continue

					cpy_letter = cpy[:1]

					if not script_move['scoreboard'][cpy_letter]:
						raise Exception("Company "+cpy_letter+" missing from script scoreboard")

					if players[player_turn]['shares'][cpy] != script_move['scoreboard'][cpy_letter]['qty']:
						raise Exception(player_turn+' has '+str(players[player_turn]['shares'][cpy])+' shares in '+cpy+'\n'+
							'Script says '+str(script_move['scoreboard'][cpy_letter]['qty']))

					if companies[cpy]['share_price'] != script_move['scoreboard'][cpy_letter]['price_per_share']:
						raise Exception(cpy+' share price is '+str(companies[cpy]['share_price'])+'\n'+
							'Script says '+str(script_move['scoreboard'][cpy_letter]['price_per_share']))

				#my $num_shares = $players[player_turn]['shares'].get('cpy', 0)
				#$companies[cpy]['share_price']

		r, c = offer_moves()
		process_move(r, c)
		buy_shares()
		turn_num += 1

	end_game()

#	my $choice2 = prompt_for_choice("Another game?", ["y", "n"])
#	if ($choice2 eq "n") {
#		last
#	}
# 	would have to add reset of @galaxy %companies @player_names %players $turn_num etc to start of loop if I was to allow another game

#----------------------------------------------------------------------------

def display_map(moves):

	#print('moves:'); pp(moves)

	print("\n                ---: MAP OF THE GALAXY :---\n")
	print("                  a b c d e f g h i j k l\n")
	for row in range(len(galaxy)):
		print('                {} '.format(row + 1), end='')
		for col in range(len(galaxy[row])):

			# if legal moves have been passed, show them

			printed = False
			if moves:
				#print Dumper $moves die
				for m in moves:
					if m['row'] == row and m['col'] == col:
					   	print('? ', end='')
					   	printed = True

			if not printed:
				if galaxy[row][col] == MARKER_A:
					print('A ', end='')
				elif galaxy[row][col] == MARKER_B:
					print('B ', end='')
				elif galaxy[row][col] == MARKER_C:
					print('C ', end='')
				elif galaxy[row][col] == MARKER_D:
					print('D ', end='')
				elif galaxy[row][col] == MARKER_E:
					print('E ', end='')
				elif galaxy[row][col] == MARKER_VACANT:
					print('· ', end='')
				elif galaxy[row][col] == MARKER_OUTPOST:
					print('+ ', end='')
				elif galaxy[row][col] == MARKER_STAR:
					print('* ', end='')

		print('{}'.format(row + 1))

	print("\n                  a b c d e f g h i j k l\n")

#----------------------------------------------------------------------------

def display_score_board():

	if turn_num > max_turns:
		info = ' - FINAL'
	else:
		info = '('+str(turn_num)+'/'+str(max_turns)+')'
	print('\nSCOREBOARD '+info+'\n')

	line_players = '                              '
	line_div     = '                              '

	for player in player_names:
		line_players += '{:12}'.format(player)
		line_div 	 += '----------- '

	lines = []
	lines.extend([line_players, line_div])

	players_share_qty_tot = {}
	players_share_qty_val = {}

	for cpy in COMPANY_NAMES:
		if cpy in companies:
			line = ' {:20} @ ${:>4}'.format(cpy, companies[cpy]['share_price'])
			for player in player_names:
				#num_shares = players[player][shares][cpy] || 0
				num_shares = players[player]['shares'].get(cpy, 0)
				line += '  {:>10}'.format(num_shares)
				if player not in players_share_qty_tot:
					players_share_qty_tot[player] = 0
				if player not in players_share_qty_val:
					players_share_qty_val[player] = 0
				players_share_qty_tot[player] += num_shares
				players_share_qty_val[player] += num_shares * companies[cpy]['share_price']
			lines.append(line)

	line_share_tot	= ' Total Share Value           '
	line_cash 		= ' Cash                        '
	line_tot 		= ' TOTAL                       '

	winning_tot = None
	winning_player = None

	for player in player_names:
		tot = players_share_qty_val.get(player, 0) + players[player]['cash']

		if not winning_tot or tot > winning_tot:
			winning_tot	= tot
			winning_player = player

		#line_share_tot	+= '  {:>10}'.format(players_share_qty_val.get(player, 0))
		line_share_tot	+= '  {:>10}'.format(players_share_qty_val.get(player, 0))
		line_cash 		+= '  {:>10}'.format(players[player]['cash'])
		line_tot 		+= '  {:>10}'.format(tot)

	lines.extend([line_div, line_share_tot, line_cash, line_div, line_tot])

	print('\n'.join(lines))

	return winning_player

#----------------------------------------------------------------------------

def offer_moves():

	# generate legal moves

	#print('script_move:'); pp(script_move)

	moves = []
	script_legal = None
	if script_move:
		script_legal = script_move['legal']

	#print('script_legal:'); pp(script_legal)

	# if ($script_move->{choice} eq '3G') {
	# 	print('\nBING!')
	# }

	for move_num in range(MAX_LEGAL_MOVES):

		while True:
			# generate a random move

			if script_move:
				if not script_legal:
					print('\nAt least one legal move in the script was rejected.\n')
					print('Script:');   pp(script_legal)
					print('Accepted:'); pp(moves)
					exit()

				m = script_legal.pop(0)
				#r, c = split //, $m
				r, c = list(m)
				move_row = int(r) - 1
				move_col = ord(c.lower()) - ord('a')
			else:
				move_row = random.randint(0, MAX_ROW - 1)
				move_col = random.randint(0, MAX_COL - 1)

			#print('Possible move {}{}'.format(move_row + 1, chr(move_col + ord('a'))))

			# check it's currently a vacant space

			if galaxy[move_row][move_col] != MARKER_VACANT:
				continue

			# check it's not the same as an existing move

			is_legal = True

			for move_num_prev in range(move_num):
				if move_row == moves[move_num_prev]['row'] and move_col == moves[move_num_prev]['col']:
				   	is_legal = False

			if not is_legal:
				continue

			is_legal = False # flip it

			# if there's a company not yet formed, it's legal

			for cpy in COMPANY_NAMES:
				if cpy not in companies:
					is_legal = True

			# if it's next to a company, it's legal
			if is_next_to_company(move_row, move_col):
				is_legal = True

			# if it's next to an outpost or star, it's legal
			# C code has a '!' (not) at the start of this condition. Is that right? what does the basic code have?
			# 1/05/2013 Well, without the not, traders_script2.txt would fall over. So I've added it.
			if not is_next_to_outpost_or_star_but_not_company(move_row, move_col):
				is_legal = True

			if is_legal:
				break

		# end while True - generate a move until it's found to be legal

		moves.append({'row': move_row, 'col': move_col})

	# end... for move_num in range(MAX_LEGAL_MOVES):

	clear_screen()
	display_score_board()
	display_map(moves)

	print('\n'+player_turn+', here are your legal moves:\n  ')
	for m in moves:
		print('{}{}, '.format(m['row'] + 1, chr(m['col'] + ord('a'))), end = '')
	print('Save game, Quit.\n')

	# process keystrokes

	while True:
		print('Your choice? ', end='')
		if script_move:
			choice = script_move['choice'].lower()
			print(choice)
		else:
			choice = input('').lower()

		if choice == 's':
			save_game()
		elif choice == 'q':
			exit('\nQUITTING!')
		else:
			m = re.match(r'^([1-9])([a-l])$', choice)
			if m:
				choice_r = m.group(1)
				choice_c = m.group(2)
			else:
				m = re.match(r'^([a-l])([1-9])$', choice)
				if m:
					choice_c = m.group(1)
					choice_r = m.group(2)
				else:
					continue

			r = c = None
			for move in moves:
				if choice_r == chr(move['row'] + ord('1')) and choice_c == chr(move['col'] + ord('a')):
					r = move['row']
					c = move['col']
			if r != None:
				break
			if script_move:
				exit('Choice in script is not a legal choice in script.')
	# while True

	#print('offer_moves is returning r={} c={}'.format(r, c))

	return r, c

#----------------------------------------------------------------------------
# Example:
# $companies[cpy]['share_price'] += $SHARE_PRICE_STD_INC + markers_count($MARKER_STAR, \@adj_markers) * $SHARE_PRICE_START_STAR

def markers_count(marker_test, markers):

	count = 0

	for m in markers:
		if marker_test == MARKER_GROUP_COMPANY:
			if m >= MARKER_A and m <= MARKER_E:
				count = 1
		else:
			if m == marker_test:
				count = 1

	return count

#----------------------------------------------------------------------------
# Example:
# if (markers_all($MARKER_VACANT, \@adj_markers)) { ... }

def markers_all(marker_test, markers):

	for m in markers:
		if m != marker_test:
			return False

	return True

#----------------------------------------------------------------------------

def is_company(marker):

	if marker >= MARKER_A and marker <= MARKER_E:
		return True

	return False

#----------------------------------------------------------------------------

def is_next_to_company(r, c):

	adj_markers = []

	if r > 0:
		adj_markers.append(galaxy[r - 1][c])
	if r < MAX_ROW - 1:
		adj_markers.append(galaxy[r + 1][c])
	if c > 0:
		adj_markers.append(galaxy[r][c - 1])
	if c < MAX_COL - 1:
		adj_markers.append(galaxy[r][c + 1])

	return markers_count(MARKER_GROUP_COMPANY, adj_markers)

#----------------------------------------------------------------------------

def is_next_to_outpost_or_star_but_not_company(r, c):

	adj_markers = []

	if r > 0:
		adj_markers.append(galaxy[r - 1][c])
	if r < MAX_ROW - 1:
		adj_markers.append(galaxy[r + 1][c])
	if c > 0:
		adj_markers.append(galaxy[r][c - 1])
	if c < MAX_COL - 1:
		adj_markers.append(galaxy[r][c + 1])

	if (markers_count(MARKER_OUTPOST, adj_markers) or markers_count(MARKER_STAR, adj_markers)) \
		and not markers_count(MARKER_GROUP_COMPANY, adj_markers):
	   	return True

	return False

#----------------------------------------------------------------------------

def process_move(r, c):

	# my %result # for checking against script
	cpy = None
	adj_markers = []
	result = {}

	global galaxy
	global companies
	global players

	if r > 0:
		adj_markers.append(galaxy[r - 1][c])
	if r < MAX_ROW - 1:
		adj_markers.append(galaxy[r + 1][c])
	if c > 0:
		adj_markers.append(galaxy[r][c - 1])
	if c < MAX_COL - 1:
		adj_markers.append(galaxy[r][c + 1])

	#pp('adj_markers:'); pp(adj_markers)

	if markers_all(MARKER_VACANT, adj_markers):
		galaxy[r][c] = MARKER_OUTPOST
	else:
		# count cpys adjacent to the chosen spot

		adj_markers_by_cpy = {}
		for m in adj_markers:
			if is_company(m):
				if MARKER_TO_COMPANY[m] not in adj_markers_by_cpy:
					adj_markers_by_cpy[MARKER_TO_COMPANY[m]] = 0
				adj_markers_by_cpy[MARKER_TO_COMPANY[m]] += 1
		#print('adj_markers_by_cpy:'); pp(adj_markers_by_cpy)

		if len(adj_markers_by_cpy) >= 2: 			# adjacent to two different companies? merge & new spot becomes largest company
			cpy, result['merge'] = merge_companies(list(adj_markers_by_cpy.keys()))
			galaxy[r][c] = COMPANY_TO_MARKER[cpy]
			# DON'T push share price up, even if there's a start adjacent
			companies[cpy]['num_markers'] += 1
		elif len(adj_markers_by_cpy) == 1:			# adjacent to one company? new spot becomes adj company
			cpy = list(adj_markers_by_cpy.keys())[0]
			galaxy[r][c] = COMPANY_TO_MARKER[cpy]
			companies[cpy]['share_price'] += SHARE_PRICE_STD_INC + markers_count(MARKER_STAR, adj_markers) * SHARE_PRICE_START_STAR
			companies[cpy]['num_markers'] += 1
		else:											# not adjacent to a company? create one, or an outpost
			#if (not markers_count($MARKER_GROUP_COMPANY, \@adj_markers))

			# toi: (in basic code)
			# tof: (in basic code) midway through?

			for cpy_test in COMPANY_NAMES:
				if cpy_test not in companies:
					cpy = cpy_test
					break
			if cpy:
				spec_ann_new_company(cpy)
				galaxy[r][c] = COMPANY_TO_MARKER[cpy]
				companies[cpy] = {}
				companies[cpy]['share_price'] = SHARE_PRICE_STD_INC + markers_count(MARKER_STAR, adj_markers) * SHARE_PRICE_START_STAR
				companies[cpy]['num_markers'] = 1
				players[player_turn]['shares'][cpy] = NUM_SHARES_FOUNDER
				result['new_cpy'] = cpy.lower()[:1]
			else:
				galaxy[r][c] = MARKER_OUTPOST
				#$result{outpost} = 1 # yep, commented out in perl
		# else
	# else

	# toj: (in basic code) - convert outpost adj to new company marker to same company

	if cpy: # ie a company marker was created

		for adj in [[r - 1, c], [r + 1, c], [r, c - 1], [r, c + 1]]:
			r_adj, c_adj = adj

			if r_adj < 0 or c_adj < 0 or r_adj > MAX_ROW - 1 or c_adj > MAX_COL - 1: # off map
				continue

			#print("r_adj={} c_adj={}".format(r_adj, c_adj))

			if galaxy[r_adj][c_adj] == MARKER_OUTPOST:

				galaxy[r_adj][c_adj] = galaxy[r][c]

				companies[cpy]['share_price'] += SHARE_PRICE_STD_INC
				companies[cpy]['num_markers'] += 1
	# end ... if company marker was created

	display_map(None)

	# iterate over companies that exist, as opposed to COMPANY_NAMES which includes non-existent companies
	for cpy_test in sorted(companies):
		#print __LINE__.": $cpy_test share_price = $companies{$cpy_test}['share_price']\n"
		if companies[cpy_test]['share_price'] >= MAX_SHARE_PRICE:
			spec_ann_split_2for1(cpy_test)
			if 'split' not in result:
				result['split'] = {}
			result['split'][cpy_test.lower()[:1]] = True

	# add interest

	#print __LINE__.": \$players[player_turn] = ".Dumper $players[player_turn]

	# As per instructions... Add stock dividends to your cash in hand (5% of the share price of your stock)
	for cpy in sorted(companies): 		# iterates over companies that exist, as opposed to @COMPANY_NAMES which includes non-existent countries
		dividend = int(0.05 * players[player_turn]['shares'].get(cpy, 0) * companies[cpy]['share_price'])
		if not dividend:
			continue
		print(player_turn+', you\'ve earned a $'+str(dividend)+' dividend for your shares in '+cpy+'.')
		players[player_turn]['cash'] += dividend

	#print('script_move = '); pp(script_move)

	if script_move:

		if turn_num == max_turns:
			result['end_game'] = {}
			#print('players:'); pp(players)
			for player in player_names:
				#print('players[player]:'); pp(players[player])
				result['end_game'][player] = {}
				result['end_game'][player]['stock_val'] = 0
				result['end_game'][player]['cash'] = players[player]['cash']
				for cpy in COMPANY_NAMES:
					if cpy in companies:
						num_shares = players[player]['shares'].get(cpy, 0)
						result['end_game'][player]['stock_val'] += num_shares * companies[cpy]['share_price']

		#print('Game result = '+yaml.dump(result))
		#print('Scripted result = '+yaml.dump(script_move['result']))

		# check result matches

		if yaml.dump(result) != yaml.dump(script_move['result']):
			#confess "Result '$result' does not match scripted result '$script_move->{result}'"
			exit('\nGame result = '+yaml.dump(result)+\
				'Scripted result = '+yaml.dump(script_move['result'])+\
				'do not match')

#----------------------------------------------------------------------------

def merge_companies(cpys):

	# Work out which company has the most markers

	merge_into_cpy = cpys[0]
	for c in cpys:
		if companies[c]['num_markers'] > companies[merge_into_cpy]['num_markers']:
			merge_into_cpy = c

	# merge others into this company

	for c in cpys:
		if c == merge_into_cpy:
			continue
		result = spec_ann_merge(merge_into_cpy, c)

	return merge_into_cpy, result

#----------------------------------------------------------------------------

def spec_ann_new_company(cpy):

	print('                Special Announcement!\n')

	print('A new shipping company has been formed. Its name is '+cpy+'.')
	print('As founder, '+player_turn+' has been allocated '+str(NUM_SHARES_FOUNDER)+' shares.\n')

#----------------------------------------------------------------------------

def spec_ann_split_2for1(cpy):

	print('                Special Announcement!\n')

	print(cpy+' stock has split 2 for 1.\n')

	companies[cpy]['share_price'] = int(companies[cpy]['share_price'] / 2)

	for p in player_names:
		if players[p]['shares'][cpy]:
			players[p]['shares'][cpy] *= 2

#----------------------------------------------------------------------------

def spec_ann_merge(merge_into_cpy, c):

	print('                Special Announcement!\n')

	print(c+' has merged into '+merge_into_cpy+'.\n')

	print('Please note the following transactions.')
	print('Old stock = '+c+'  New stock = '+merge_into_cpy)
	print('               old       new          total         bonus')
	print(' Player        stock     stock        holdings      paid')

	result = {}
	result['new_cpy'] = merge_into_cpy[:1].lower()
	result['old_cpy'] = c[:1].lower()
	result['by_player'] = {}

	shares_all_players = 0
	for player in player_names:
		shares_all_players += players[player]['shares'][c]

	for player in player_names:
		bonus = int(10 * companies[c]['share_price'] * players[player]['shares'][c] / shares_all_players)
		old_shares_now_new = int((players[player]['shares'][c] + 1) / 2)
		players[player]['shares'][merge_into_cpy] += old_shares_now_new
		players[player]['cash'] += bonus

		#        Player        stock     stock        holdings      paid
		#		 123456789 123456789 123456789 123456789012345 123456789

		# %-9s %9s %9s %15s %9s
		print(' {:<9} {:9} {:9} {:15} {:>10}'.format(
			player,
			players[player]['shares'][c],
			old_shares_now_new,
			players[player]['shares'][merge_into_cpy],
			'$'+str(bonus),
		))

		result['by_player'][player] = {}
		result['by_player'][player]['old_s'] = players[player]['shares'][c]
		result['by_player'][player]['new_s'] = old_shares_now_new
		result['by_player'][player]['total'] = players[player]['shares'][merge_into_cpy]
		result['by_player'][player]['bonus'] = bonus

		players[player]['shares'][c] = 0

	for row in range(MAX_ROW):
		for col in range(MAX_COL):
			if galaxy[row][col] == COMPANY_TO_MARKER[c]:
				galaxy[row][col] = COMPANY_TO_MARKER[merge_into_cpy]

	companies[merge_into_cpy]['num_markers'] += companies[c]['num_markers']
	companies[merge_into_cpy]['share_price'] += companies[c]['share_price']
	del companies[c]

	return result

#----------------------------------------------------------------------------

def buy_shares():
	# end_chosen_pos_processing: (in basic code)

	# TOL means end of turn, so reverse logic - huh?

	#print __LINE__.": \$players[player_turn]['shares'] = ".Dumper $players[player_turn]['shares']
	#print __LINE__.": \%companies = ".					  Dumper \%companies

	#if script_move:
		#print __LINE__.": \$script_move->['buy'] = ".Dumper $script_move->['buy']

	# --> Should we continue to just iterate though (sort keys %companies)???
	# This means the player can't first sell E to fund purchase of A. Or do we stay true to the original?

	for cpy in sorted(companies):		# iterates over companies that exist, as opposed to @COMPANY_NAMES which includes non-existent countries

		# TOM: (in basic code)
		# TOQ: (in basic code)
		# previous code checked if the player afford a share in the company, but what if they want to sell?

		#print __LINE__.": \$players[player_turn]['shares'][cpy] = ".Dumper $players[player_turn]['shares'][cpy]
		#print __LINE__.": \$companies[cpy]['share_price'] = ".		Dumper $companies[cpy]['share_price']

		num_shares = players[player_turn]['shares'].get(cpy, 0)
		print('\n'+player_turn+', you own '+str(num_shares)+' '+cpy+' shares valued at $'+str(companies[cpy]['share_price'])+' each.')
		print('You have $'+str(players[player_turn]['cash'])+' cash.')

		buy_min = 0
		if num_shares:
			buy_min = 1 - num_shares # actually sell_max. at least one share must be retained
		buy_max = int(players[player_turn]['cash'] / companies[cpy]['share_price'])

		if script_move:
			#print('Before pop\'ing '+cpy+':'); pp(script_move['buy'])
			choice = script_move['buy'].pop(cpy.lower()[:1], 0)
			#print('After:'); pp(script_move['buy'])
			print('Buying '+str(choice)+' shares')

			if 'price' in script_move and cpy in script_move['price']:
				#print STDERR "Checking $script_move->['price'][cpy] vs $companies[cpy]['share_price']\n"
				if script_move['price'][cpy] != companies[cpy]['share_price']:
					# Timing issue here - traders_script2.txt causes Altair: script price=1900, actual price=2400
					exit(cpy+': script price='+script_move['price'][cpy]+' actual price='+companies[cpy]['share_price'])
		else:
			while True:
				choice = input('How many shares would you like to buy ('+str(buy_max)+' at most) or sell ('+str(buy_min)+' at most) ? ')
				if choice == '':
					choice = '0'

				if represents_int(choice):
					choice = int(choice)
					if choice >= buy_min and choice <= buy_max:
						break

		# TON: (in basic code)
		# if statement in original code just sets max sell amount so that at least one share is retained. done above.
		if not cpy in players[player_turn]['shares']:
			players[player_turn]['shares'][cpy] = 0
		players[player_turn]['shares'][cpy] += choice
		players[player_turn]['cash'] -= choice * companies[cpy]['share_price']

	if script_move and 'buy' in script_move:
		err = []
		for c in sorted(script_move['buy']):
			if script_move['buy'][c]:
				err.append(c)

		if err:
			exit('Script error: Unactioned buys for '+str(err)+' = '+str(script_move['buy']))

#----------------------------------------------------------------------------

def end_game():

	print('                Special Announcement!\n')

	winning_player = display_score_board()

	print('\n'+winning_player+' is the winner! Congratulations!')

#----------------------------------------------------------------------------

def save_game():

	g = {\
		'galaxy': 		galaxy,
		'companies': 	companies,
		'player_names':	player_names,
		'players': 		players,
		'max_turns': 	max_turns,
		'turn_num': 	turn_num,
		'player_turn': 	player_turn,
	}

	# Re Tk... See comment in load_game()
	# root = tk.Tk()
	# root.withdraw()
	# fn = filedialog.asksaveasfilename(initialdir = os.getcwd(), title = "Save file", filetypes = (("Star Lanes game files","*.sl.json"),("All files","*")))

	app = wx.App(None)
	style = wx.FD_SAVE
	dialog = wx.FileDialog(None, 'Save as', wildcard='*.sl.json', style=style)
	if dialog.ShowModal() == wx.ID_OK:
		fn = dialog.GetPath()
	else:
		exit()
	dialog.Destroy()

	with open(fn, 'w') as fp:
		#json.dump(g, fp, *, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, cls=None, indent=None, separators=None, default=None, sort_keys=False, **kw)
		json.dump(g, fp, indent=1)
	print('\nGame saved!\n')

#----------------------------------------------------------------------------

def load_game():

	global galaxy
	global companies
	global player_names
	global players
	global max_turns
	global turn_num
	global player_turn

	# Tk is not passing focus back to console after selecting file.
	#root = tk.Tk()
	#root.withdraw()
	#fn = filedialog.askopenfilename(initialdir = os.getcwd(), title = "Select file", filetypes = (("Star Lanes game files","*.sl.json"),("All files","*")))

	# Trying wxPython. If it doesn't do it for me, try win32ui or easygui or pywin32.
	app = wx.App(None)
	style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
	dialog = wx.FileDialog(None, 'Open', wildcard='*.sl.json', style=style)
	if dialog.ShowModal() == wx.ID_OK:
		fn = dialog.GetPath()
	else:
		exit()
	dialog.Destroy()

	with open(fn, 'r') as fp:
		#json.load(fp, *, cls=None, object_hook=None, parse_float=None, parse_int=None, parse_constant=None, object_pairs_hook=None, **kw)
		g = json.load(fp)
	galaxy 		= g['galaxy']
	companies 	= g['companies']
	player_names= g['player_names']
	players 	= g['players']
	max_turns	= g['max_turns']
	turn_num 	= g['turn_num']
	player_turn = g['player_turn']

	print('\nGame loaded!\n')

#----------------------------------------------------------------------------

def setup_new_game():

	global galaxy

	for row in range(MAX_ROW):
		galaxy.append([])
		for col in range(MAX_COL):
			galaxy[row].append(MARKER_VACANT)

	if script_moves:
		m = script_moves[0]['map_before'] # script_move not assigned yet
		#pp(m); exit('Ugh')
		for row in range(len(m)):
			cols = list(m[row])
			for col in range(len(cols)):
				if cols[col] == '*':
					galaxy[row][col] = MARKER_STAR
	else:
		# Assign stars to between 3 and 7 positions
		for _ in range(3, random.randint(3, 7 + 1)):
			galaxy[random.randrange(MAX_ROW)][random.randrange(MAX_COL)] = MARKER_STAR

	global turn_num
	turn_num = 1

	global player_names

	if script_players != None:
		player_names = script_players
	else:
		while True:
			num_players = input('How many players (2 to 4) ? ')
			if num_players.lower() == 'q':
				exit()
			if num_players.isdigit():
				num_players = int(num_players)
				if num_players >= 2 and num_players <= 4:
					break

		print('')

		for i in range(1, num_players + 1):
			while True:
				p = input('Please enter the name of player '+str(i)+': ')
				if p != '':
					break
			player_names.append(p)

		# mix up player_names
		from random import shuffle
		shuffle(player_names)

	global players
	for p in player_names:
		players[p] = {}
		players[p]['cash'] = STARTING_CASH
		players[p]['shares'] = {}

	print('\n'+player_names[0]+' will have the first turn.\n')

	# My addition. Due we stay true to the original and hardcode 48? (the classic number of turns)
	global max_turns
	max_turns = TURNS['s']

#	do {
#		printf "Short/Classic (%d turn), Medium (%d turn) or Long (%d turn) game (s/m/l) ? ", $TURNS{s}, $TURNS{m}, $TURNS{l}
#		my $t = <STDIN>
#		chomp $t
#		$max_turns = $TURNS{lc $t}
#	}
#	while (not $max_turns)

#----------------------------------------------------------------------------

def represents_int(s):
	try:
		int(s)
		return True
	except ValueError:
		return False

#----------------------------------------------------------------------------

def clear_screen():

	#_ = input('Press <Enter> to clear screen')
	os.system('cls' if os.name=='nt' else 'clear')

#----------------------------------------------------------------------------
# main

parser = argparse.ArgumentParser('Star Lanes')
parser.add_argument('--script')
args = parser.parse_args()

if args.script:
	script = Script.read_script(args.script)
	#print('script = '); pp(script)
	script_moves = script['moves']
	script_players = script['players']
#	script_first_player = script['first_player']
#else:
#	exit('No script specified')

play_game()

#----------------------------------------------------------------------------
# end
