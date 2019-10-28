'''
Game flow...

jock - first
fred

map (stars only)

turn
	legal moves
	chosen move

	special announcement?

	buy/sell shares?

	check map is consistent

	check scoreboard is consistent

winner

'''

import re
from pprint import pprint as pp

line = ''
lines = []
line_num = 0

# -------------------------------------------------------------------------------

def read_script(fn_in):

	global line
	global lines
	global line_num

	with open(fn_in) as f:
		lines = f.read().splitlines()

	lines = [line.strip() for line in lines]
	#print('lines ='); pp(lines)

	line_num = 0

	players2 = []

	while True:
		get_line()
		if     line == "traders.exe" \
			or line == "**********   STAR TRADERS   **********" \
			or line == "THE CLASSIC GAME WRITTEN BY S.J. SINGER" \
			or line == "?" \
			or re.match(r'^HOW MANY PLAYERS  \(2-4\)  \? \d$', line) \
			or line ==  "DOES ANY PLAYER NEED INSTRUCTIONS  ? n":
			continue
		m = re.match(r'PLAYER         \d             WHAT IS YOUR NAME  \? (\w+)$', line)
		if m:
			#pp(m)
			players2.append(m.group(1))
		else:
			if players2:
				break
			raise Exception('Unexpected line:\n{}\nMissing player. Line {}.'.format(line, line_num))

	#print('players2=...'); pp(players2)

	m = re.match(r'^(\w+) IS THE FIRST PLAYER TO MOVE\.$', line)
	if not m:
		raise Exception('Unexpected line:\n{}\nMissing first player. Line {}.'.format(line, line_num))
	first_player = m.group(1)

	get_line()
	m = re.match(r'^\[order=(.+)\]$', line)
	if not m:
		raise Exception('Unexpected line:\n{}\nMissing [order=player|player...]. Line {}.'.format(line, line_num))
	players = m.group(1).split('|')
	#print('players=...'); pp(players)
	if players[0] != first_player:
		raise Exception(first_player+' should be first in [order=player|player...]')

	moves = []
	
	get_line()

	while True:

		move = {}
		move['result'] = {}

		if line == "?" \
		   or line == "WHAT IS YOUR MOVE ? M":
			get_line()
			continue

		if not re.match(r'^MAP OF THE GALAXY$', line):
			raise Exception('Unexpected line:\n'+line+'\nMissing map. Line '+str(line_num)+'.')
		move['map_before'] = get_map()

		get_line()
		m = re.match(r'^(\w+), HERE ARE YOUR LEGAL MOVES FOR THIS TURN$', line)
		if not m:
			raise Exception('Unexpected line:\n'+line+'\nMissing legal moves heading. Line '+str(line_num)+'.')
		move['player'] = m.group(1)

		#-->check it is the expected player

		get_line()
		if not re.match(r'^\d [A-L]  \d [A-L]  \d [A-L]  \d [A-L]  \d [A-L]$', line):
			raise Exception('Unexpected line:\n'+line+'\nMissing legal moves. Line '+str(line_num)+'.')
		legals = line.split('  ')
		for i in range(len(legals)):
			legals[i] = legals[i].replace(' ', '')
		move['legal'] = legals

		get_line()
		# --> Perl code has label here...
		#MOVE:
		# if (/^WHAT IS YOUR MOVE \? M$/) {
		#     get_map()
		#
		if re.match(r'^WHAT IS YOUR MOVE \? S$', line):
			move['scoreboard'] = get_scoreboard()
			#get_line() # In perl... goto MOVE;

		m = re.match(r'^WHAT IS YOUR MOVE \? (\d[A-L])$', line)
		if m:
			move['choice'] = m.group(1)
		else:
			m = re.match(r'^\[choice=(\d[A-L])\]$', line, re.IGNORECASE)
			if m:
				move['choice'] = m.group(1).upper()
			else:
				m = re.match(r'^\[(\d[A-L])\]$', line, re.IGNORECASE)
				if m:
					move['choice'] = m.group(1).upper()
				elif re.match(r'^\[end\]$', line, re.IGNORECASE):
					break
				else:
					raise Exception('Unexpected line:\n'+line+'\nMissing choice. Line '+str(line_num)+'.')

		if move['choice'] not in move['legal']:
			raise Exception('Choice '+move['choice']+' is not one of the legal moves:\n'+' '.join(move['legal'])+'\nLine '+str(line_num)+'.')

		get_line()
		if line == '?':
			get_line()
		if line == 'SPECIAL ANNOUNCEMENT !!!':
			get_line()

		if line == 'A NEW SHIPPING COMPANY HAS BEEN FORMED !':
			get_line()
			m = re.match(r'^IT\'S NAME IS  \'(.+?)\'$', line)
			if not m:
				raise Exception('Unexpected line:\n'+line+'\nMissing new company name. Line '+str(line_num)+'.')
			move['result']['new_cpy'] = m.group(1).lower()[:1]
			get_line()

		m = re.match(r'\'(.+?)\' HAS JUST BEEN MERGED INTO \'(.+?)\'', line)
		if m:
			old_cpy = m.group(1).lower()[:1]
			new_cpy = m.group(2).lower()[:1]
			#raise Exception(m.group(1) - m.group(2))

			res = {'old_cpy': old_cpy, 'new_cpy': new_cpy}

			get_line()
			if not re.match(r'^PLEASE NOTE THE FOLLOWING TRANSACTIONS.$', line):
				raise Exception('Unexpected line:\n'+line+'\nMissing merge note. Line '+str(line_num)+'.')

			get_line()
			if not re.match(r'^OLD STOCK', line):
				raise Exception('Unexpected line:\n'+line+'\nMissing merge companies. Line '+str(line_num)+'.')

			get_line()
			if not re.match(r'^PLAYER   OLD STOCK   NEW STOCK   TOTAL HOLDINGS     BONUS PAID$', line):
				raise Exception('Unexpected line:\n'+line+'\nMissing merge titles. Line '+str(line_num)+'.')

			while True:
				get_line()
				m = re.match(r'^(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+\$ (\w+)$', line)
				if not m:
					break
				if 'by_player' not in res:
					res['by_player'] = {}
				res['by_player'][m.group(1)] = {
					'old_s': int(m.group(2)), 
					'new_s': int(m.group(3)), 
					'total': int(m.group(4)), 
					'bonus': int(m.group(5))
				}

			if 'by_player' not in res:
				raise Exception('Unexpected line:\n'+line+'\nMissing merge table. Line '+str(line_num)+'.')

			move['result']['merge'] = res

		if line == 'SPECIAL ANNOUNCEMENT !!!':
			get_line()

		while True:
			m = re.match(r'^THE STOCK OF  \'(.+?)\'\s+HAS SPLIT 2 FOR 1 \!$', line)
			if not m:
				break
			#($cpy) = split /[\s\,]/, ucfirst lc $cpy
			#cpy_words = m.group(1).split()
			#cpy = cpy_words[0].title()
			cpy = m.group(1).lower()[:1]
			if 'split' not in move['result']:
				move['result']['split'] = {}
			move['result']['split'][cpy] = True # there may be more than one split --> hence 'while True:'? or should this be + 1
			get_line()

		while True:

			#print __PACKAGE__." ".__LINE__.": $_\n"

			if re.match(r'^YOUR CURRENT CASH= \$ \d+$', line):
				get_line()

			price = None

			#BUY HOW MANY SHARES OF 'ALTAIR STARWAYS' AT $ 2825

			m = re.match(r'^BUY HOW MANY SHARES OF \'(.+)\' AT \$\s*(\d+)', line)
			if m:
				cpy = m.group(1).lower()[:1]
				price = m.group(2)
				get_line()
				m = re.match(r'^YOU NOW OWN\s+-?\d+ \?\s*(\d+)$', line)
				if not m:
					raise Exception('Unexpected line:\n'+line+'\nMissing new own amount. Line '+str(line_num)+'.')
				qty = m.group(1)

			else:
				m = re.match(r'^\[BOUGHT (\d+) SHARES? IN (.+)\]', line)
				if m:
					qty = m.group(1)
					cpy = m.group(2).lower()[:1]

				else:
					m = re.match(r'^\[B (\w) (-?\d+)\]', line, re.IGNORECASE)
					if m:
						cpy = m.group(1).lower()[:1]
						qty = m.group(2)
						#CPYS = {'a': 'Altair', 'b': 'Betelgeuse', 'c': 'Capella', 'd': 'Denebola', 'e': 'Erandini'}
						#cpy = CPYS[cpy]

					else:
						break

			if 'buy' not in move:
				move['buy'] = {}
			move['buy'][cpy] = int(qty)

			if price:
				if 'price' not in move:
					move['price'] = {}
				move['price'][cpy] = price

			get_line()

		#                THE GAME IS OVER - HERE ARE THE FINAL STANDINGS
		# PLAYER   CASH VALUE OF STOCK    CASH ON HAND
		#                                                  NET WORTH
		# andrew   $ 374200               $ 138790         $ 512990
		# alex     $ 286000               $ 109394         $ 395394
		#
		# PRESS ANY KEY TO RETURN TO MENU

		if re.match(r'^THE GAME IS OVER - HERE ARE THE FINAL STANDINGS$', line):

			get_line()
			if not re.match(r'^PLAYER   CASH VALUE OF STOCK    CASH ON HAND$', line):
				raise Exception('Unexpected line:\n'+line+'\nMissing end of game headings. Line '+str(line_num)+'.')

			get_line()
			if not re.match(r'^NET WORTH$', line):
				raise Exception('Unexpected line:\n'+line+'\nMissing end of game headings. Line '+str(line_num)+'.')

			while True:
				get_line()
				if line == None:
					break
				r = re.compile(r'\$\s+')	# remove spaces after $'s
				line = r.sub('$', line)
				m = re.match(r'^(\w+)\s+\$(\d+)\s+\$(\d+)\s+\$(\d+)$', line)
				if not m:
					break
				if int(m.group(2)) + int(m.group(3)) != int(m.group(4)):
					raise Exception('Bad game result:\n'+line+'\nLine '+str(line_num)+'.')
				if 'end_game' not in move['result']:
					move['result']['end_game'] = {}
				move['result']['end_game'][m.group(1)] = {'stock_val': int(m.group(2)), 'cash': int(m.group(3))}

		if 'buy' not in move:
			raise Exception('Unexpected line:\n'+line+'\nMissing buy amount. Line '+str(line_num)+'.')

		for k in ['legal', 'choice']:
			if k not in move:
				raise Exception('move is missing '+k)

		#print('move:'); pp(move)

		moves.append(move)

		if 'end_game' in move['result']:
			break

	#print __PACKAGE__." ".__LINE__.": moves = ".Dumper \@moves

	#if (@lines)
	#   raise Exception('\nUnhandled lines remain. First unhandled line:\n$lines[0]\n  "
	#

	return { 'moves': moves, 'players': players, 'first_player': first_player }

# ----------------------------------------------------------------------------

def get_line():

	global lines
	global line_num
	global line

	line = ''
	while line == '' or line.startswith('//'):
		line_num += 1
		if lines:		
			line = lines.pop(0)
		else:
			line = None
			break

# ----------------------------------------------------------------------------

def get_map():

	global line

	mp = []
	get_line()
	if line != "*******************":
		raise Exception('Unexpected line:\n'+line+'\nMissing map star heading. Line '+str(line_num)+'.')
	get_line()
	if line != "A  B  C  D  E  F  G  H  I  J  K  L":
		raise Exception('Unexpected line:\n'+line+'\nMissing map col headings. Line '+str(line_num)+'.')
	for row in range(1, 9+1):
		get_line()
		m = re.match(r'^'+str(row)+'   (.+)$', line)
		if not m:
			raise Exception('Unexpected line:\n'+line+'\nMissing map row. Line '+str(line_num)+'.')
		mp.append(m.group(1).replace(' ', '').replace('.', ' '))
		# $mp[-1] =~ s/ //g
		# $mp[-1] =~ s/\./ /g

	#print('Map:'); pp(mp); #exit('Ugh')

	return mp

# ----------------------------------------------------------------------------

def check_map(actual, script):

	#print('check_map - actual:'); pp(actual)
	#print('check_map - script:'); pp(script)

	actual_strs = []
	# my @rows_diff

	for row in actual:
		actual_strs.append(''.join(row))
		# if ($actual_rows[$row] ne $script->[$row])
		# 	push @rows_diff, $row

	#print('check_map - actual_strs:'); pp(actual_strs)

	if ''.join(actual_strs) != ''.join(script):
		print('Actual:'); pp(actual_strs)
		print('Script:'); pp(script)
		raise Exception('Actual map differs from script map. See above.')
		#confess "Differ at row(s) [@rows_diff]"

# ----------------------------------------------------------------------------

def get_scoreboard():

	global line

	# STOCK                        PRICE PER SHARE     YOUR HOLDINGS
	# 'ALTAIR STARWAYS'             900                 4
	# 'BETELGEUSE,LTD.'             600                 3
	# 'CAPELLA FREIGHT CO.'         300                 -8

	s = {}
	get_line()
	if re.match(r'^\?$', line):
		get_line()

	if line != "STOCK                        PRICE PER SHARE     YOUR HOLDINGS":
		raise Exception('Unexpected line:\n'+line+'\nMissing scoreboard heading. Line '+str(line_num)+'.')

	while True:
		get_line()
		m = re.match(r'\'(\w).+?\'\s+(\d+)\s+(-?\d+)$', line)
		if m:
 			s[m.group(1)] = {'price_per_share': int(m.group(2)), 'qty': int(m.group(3))}
		else:
 			break

	#print __PACKAGE__." ".__LINE__.": scoreboard = ".Dumper \%s

	return s

# ----------------------------------------------------------------------------
# end
