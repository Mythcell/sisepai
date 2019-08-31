#!/usr/bin/env python3
"""
This file contains the key functions and game logic needed to simulate
a complete n-player game of Sisepai.

(c) 2019 Mitchell Cavanagh
"""

import sisepai as ssp
import numpy as np
import math

def construct_deck(nplayers):
    """Constructs an appropriately sized deck given the number of players"""
    global deck
    if nplayers < 2:
        deck=ssp.Deck(ndecks=1)
    elif nplayers <= 4:
        deck=ssp.Deck()
    else:
        deck=ssp.Deck(ndecks=math.floor((nplayers+1)/2))

def setup_game(agents):
    """Populates the player array, builds the overall deck and deals cards to all players"""
    global players; global current_player; global active_card
    global discards; global faceup_sets; global turn_count

    #Reset key variables
    active_card=None; turn_count=0

    #Initialise key arrays
    discards=[]; faceup_sets=[]

    #Setup the player array with either the supplied list of agents
    players=[a for a in agents]

    construct_deck(len(players))
    #Randomly choose the player to start first
    fp = np.random.choice(range(len(players)),1)[0]
    current_player=fp

    #Deal cards to all players
    for p in players: p.give_cards(deck.draw_cards(20))
    #Deal an extra card to the player to start first
    players[fp].give_cards(deck.draw_cards(1))

    if verbose: print('Player',fp,'starts')

def check_oot(drawn=False):
    """Determines if any players can meld out of turn.  If so, sets the current player index to
    the player with the highest meld priority.  Returns 'next' if a player other than the current
    player can out-of-turn meld, or 'meld' otherwise."""
    global players; global current_player; global active_card

    cp=current_player
    oot_sets=[]
    for p in players: oot_sets.append(p.check_meld(active_card=active_card))

    #check for 4-of-a-kind melds
    for i in range(len(players)):
        if oot_sets[cp] != None:
            if ssp.is_identical_set(oot_sets[cp]) and len(oot_sets[cp].cards)==4:
                if cp == (current_player + 1) % len(players):
                    return 'meld' #continue as normal if the next player can meld
                current_player=cp #shift priority to the first player found
                return 'oot'
        cp = (cp + 1) % len(players)
    #4-colour beats 3-of-a-kind, but can only be melded by the current player
    if oot_sets[cp] != None:
        if ssp.is_four_colour_set(oot_sets[cp]): return 'meld' #no need to update current_player
    #otherwise check for 3-of-a-kind melds
    for i in range(len(players)):
        if oot_sets[cp] != None:
            if ssp.is_identical_set(oot_sets[cp]) and len(oot_sets[cp].cards)==3:
                if cp == (current_player + 1) % len(players):
                    return 'meld' #continue as normal if the next player can meld
                current_player=cp #shift priority to the first player found
                return 'oot'
        cp = (cp + 1) % len(players)
    return 'meld' #default


def conduct_turn(oot_turn=False):
    """Conducts a turn of Sisepai, updates field variables, and determines the next player to play"""
    #Get the key gameplay variables
    global deck; global players; global current_player
    global faceup_sets; global discards; global active_card
    global turn_count;

    if verbose: print('') #start a new line for readibility

    #Give each player the updated field information
    for p in players: p.update_field_info(discards,faceup_sets)

    if len(players[current_player].collection) == 21 and active_card == None:
        active_card=players[current_player].discard_card()
        active_card.active=True
        if verbose: print(players[current_player].name,'discards',active_card,'to start the game.')
        current_player = (current_player + 1) % len(players)
        return 'next'
    else:
        #If there are no cards left in the deck, the discarded cards form the new deck
        if len(deck.cards) == 0:
            #This is near impossible in a real-life game, but is included for safety
            if len(discards) == 0:
                print('Out of cards; game ends.')
                return 'exit'
            for c in discards: deck.cards.append(c)
            deck.shuffle_deck()
            if verbose: print('Deck empty; reshuffling all discards.')

        #This also should not happen for there should always be an active card at the end of every turn
        if active_card == None:
            print('An active card has gone missing; drawing another from the deck.')
            active_card=deck.draw_active_card()

        #Conduct the player's turn
        if verbose and active_card.active==True: print('The active card is',active_card)

        if oot_turn:
            #Players cannot be given the option to draw a card if they are melding out-of-turn
            ms, x = players[current_player].play_turn(active_card=active_card,drawn=True,return_set=True)
        else:
            ms, x = players[current_player].play_turn(active_card=active_card,return_set=True)

        if x == 'draw':
            #The ununsed active card is added to the global discard pile...
            discards.append(active_card)
            #...and a new card from the deck becomes the active card
            active_card=deck.draw_active_card()
            if verbose: print(players[current_player].name,'draws',active_card)

            #As a new card has been drawn, we must first check if anyone else can meld with it
            if (not oot_turn) and enable_oot:
                oot=check_oot(drawn=True)
                if oot == 'oot':
                    if verbose: print(players[current_player].name,'calls for an out-of-turn meld')
                    return 'oot'

            #Otherwise the current player can continue normally
            ms, x = players[current_player].play_turn(active_card=active_card,drawn=True,return_set=True)
            if x == 'kaeu':
                if verbose: print(players[current_player].name,'melds',ms)
                return 'win'

        elif x == 'kaeu':
            if verbose: print(players[current_player].name,'melds',ms)
            return 'win'

        #If the player has melded a set, then add that set to the global list of faceup sets
        if ms != None:
            faceup_sets.append(ms)
            if verbose: print(players[current_player].name,'melds',ms)
        if verbose: print(players[current_player].name,'discards',x)
        active_card = x
        #We only consider the turn complete once a card is discarded
        turn_count += 1

        #Check for out-of-turn melding with this new active card
        if (not oot_turn) and enable_oot:
            oot=check_oot()
            if oot == 'oot':
                if verbose: print(players[current_player].name,'calls for an out-of-turn meld')
                return 'oot'

        #Otherwise pass on the turn normally
        current_player = (current_player + 1) % len(players)
        return 'next'

def play_game(nplayers=4,agents=[],nturns=0,is_verbose=True,with_oot=True):
    """Simulates a game of Sisepai.  Uses the supplied list of agents, otherwise runs
    the game with [nplayers] players using the default functionality.
    If a list of agents is supplied then this overwrites [nplayers].
    If nturns is supplied with a positive value, the game is simulated for [nturns] turns.
    Otherwise the game continues until a player wins or an exit case is reached.
    Out-of-turn melding can be toggled; so too can verbose output."""

    global enable_oot
    enable_oot=with_oot if nplayers > 2 else False
    global verbose; verbose=is_verbose

    #If a list of agents is provided then the game will be setup with those irrespective of whatever nplayers was set to
    if len(agents) > 0:
        if verbose: print('Setting up game with supplied list of agents')
        setup_game(agents)
    else:
    #Otherwise setup the game with [nplayers] default agents
        if verbose: print('Setting up game with',nplayers,'default agents')
        setup_game([ssp.Player(name='Player '+str(i)) for i in range(nplayers)])

    oot=False
    #Either play until someone wins...
    if nturns < 1:
        while True: #(MAIN GAME LOOP)
            if oot:
                result = conduct_turn(oot_turn=True)
            else:
                result = conduct_turn()

            if result=='win' or result=='exit': break

            if result=='oot': oot=True
            else: oot=False

        if verbose:
            print('\nPlayer',current_player,'wins with a score of',players[current_player].total_score)
            print('This game took',turn_count,'turns')

    #...or simulate game for nturns turns
    elif nturns > 0:
        for i in range(nturns):
            if oot:
                result = conduct_turn(oot_turn=True)
            else:
                result = conduct_turn()

            if result=='win' or result=='exit': break

            if result=='oot': oot=True
            else: oot=False

        if verbose:
            print('\nPlayer',current_player,'wins with a score of',players[current_player].total_score)
            print('This game took',turn_count,'turns')

    else: print('Invalid turn argument')

if __name__ == '__main__':
    play_game()
