#!/usr/bin/env python3
"""
This file contains the classes for all the core game objects in Sisepai,
along with several general functions for hand evaluations, etc.

(c) 2019 Mitchell Cavanagh
"""
import numpy as np #required for random shuffling, etc

class Card():
    """Models a Sisepai Card."""

    validSuits=["kuin","tse","xiong","kee","mah","pau","chut"]
    validColours=["red","yellow","white","green"]

    def __init__(self, colour=None, suit=None, active=False):
        """Default constructor"""
        self.active=active; self.locked=False
        if colour in self.validColours and suit in self.validSuits:
            self.colour=colour
            self.suit=suit
            self.rank=self.calculate_rank()
        else: #Some default values for an invalid card construction
            self.colour='invalid'; self.suit='invalid'; self.rank=100

    def calculate_rank(self):
        """Determine the rank of the card (from 0 to 27)"""
        return (4*self.validSuits.index(self.suit)+4-(len(self.validColours)-
            self.validColours.index(self.colour)))

    def lock(self): self.locked=True

    def unlock(self): self.locked=False

    def __repr__(self):
        return "[%s, %s]" % (self.colour, self.suit)

class Deck():
    """Models a deck of Sisepai cards"""

    def __init__(self, ndecks=2, shuffle=True):
        self.ndecks=ndecks
        self.cards=self.populate_deck(self.ndecks)
        if shuffle: self.shuffle_deck()

    def populate_deck(self, ndecks=2):
        """Creates a list of [ndeck] decks of sisepai cards"""
        cards=[]; c=Card()
        for i in c.validSuits:
            for j in c.validColours:
                for k in range(4*ndecks):
                    cards.append(Card(j,i))
        del c; return cards

    def draw_active_card(self, shuffle=False):
        """Draws and returns a single card from the deck and makes it active"""
        if shuffle: self.shuffle_deck()
        if len(self.cards) < 1: return None
        c=self.cards.pop()
        c.active=True
        return c

    def draw_cards(self, ncards=1, shuffle=False):
        """Draws [ncards] from the deck.  Returns a list. Each card is inactive"""
        if shuffle: self.shuffle_deck()
        if len(self.cards)-ncards < 1: return None #POTENTIALLY CHANGE THIS CONDITION
        dcards=[]
        for i in range(ncards): dcards.append(self.cards.pop())
        return dcards

    def print_deck(self):
        for i in self.cards: print(i)

    def reshuffle_deck(self):
        """Reconstructs and shuffles deck according to original size"""
        self.cards=self.populate_deck(self.ndecks)
        self.shuffle_deck()

    def shuffle_deck(self):
        """Shuffles the deck using np.random.shuffle"""
        np.random.shuffle(self.cards)

    def sort_deck(self):
        self.cards.sort(key=lambda x: x.rank)

    def __repr__(self):
        return "%d cards left" % len(self.cards)

class Set():
    """Models a set of cards in Sisepai."""

    def __init__(self, cards=None):
        self.cards=cards
        self.melded=contains_active_card(cards)
        self.invalid=False
        self.same_colour=cards_same_colour(cards)
        self.same_suit=cards_same_suit(cards)
        self.unique_colours=cards_unique_colours(cards)
        self.score=self.evaluate_score()

    def evaluate_score(self):
        """Determines the score of a set as per the rules of Sisepai"""
        if self.same_suit and self.cards[0].suit != 'kuin':
            if self.same_colour:
                if len(self.cards) == 4: return 6 if self.melded else 8 #4-of-a-kind
                if len(self.cards) == 3: return 1 if self.melded else 3 #3-of-a-kind
                if len(self.cards) == 2: return 0 #pair
            if self.unique_colours and self.cards[0].suit == 'chut':
                if len(self.cards) == 4: return 4 #4-colour-chut
                if len(self.cards) == 3: return 1 #3-colour chut
        if self.same_colour:
            suits=sorted([i.suit for i in self.cards])
            if suits==sorted(["kuin","tse","xiong"]): return 2
            if suits==sorted(["kee","mah","pau"]): return 1
        if self.cards[0].suit == 'kuin' and len(self.cards) == 1: return 1
        self.invalid=True; return -1

    def __repr__(self):
        return "%s" % self.cards

class Player():
    """Models a basic player of Sisepai."""

    def __init__(self, name='test'):
        self.name=name
        self.field_discards=[] #store all the discarded cards visible on the field
        self.field_melded_sets=[] #store all the melded sets visible on the field
        self.total_score=0 #score of player's collection (hand, facedowns, melds)
        self.hand=[] #all cards in current hand
        self.hand_sets=[] #sets in current hand
        self.hand_score=0 #score of all cards in the hand
        self.facedown_sets=[] #dealt sets placed face down
        self.facedown_score=0 #score of facedown sets
        self.melded_sets=[] #melded sets placed face up
        self.melded_score=0 #score of melded sets
        self.lang_pai=[] #loose cards
        self.collection=[] #list of ALL cards

    def give_cards(self, cards):
        """Deal the player cards (essentially a second constructor)"""
        for i in cards: self.hand.append(i)
        self.hand=sort_cards(self.hand)
        self.separate_facedown_sets() #remove facedown_sets
        self.evaluate_player_hand() #now evaluate the remaining hand

    def separate_facedown_sets(self):
        """In sisepai it is customary to place dealt sets that cannot be further
        improved (such as 4-of-a-kinds and 4-colour chut) face-down on the table.
        This function separates these ``terminal'' dealt sets from the player hand"""
        fs, hs, lp = evaluate_hand(self.hand,return_sets=True)
        for s in fs:
            if len(s.cards) == 4 and cards_same_suit(s.cards):
                #Only remove the 4-colour chut from the hand if there are
                #no other chut in the player's hand (as is customary)
                if cards_unique_colours(s.cards):
                    th=[c for c in self.hand]
                    for c in s.cards: th.remove(c)
                    if not hand_contains_suit(th,'chut'):
                        self.facedown_sets.append(s)
                        for c in s.cards: self.hand.remove(c)
                        self.facedown_score += s.score
                #Otherwise 4-of-a-kinds can be removed immediately
                elif cards_same_colour(s.cards):
                    self.facedown_sets.append(s)
                    for c in s.cards: self.hand.remove(c)
                    self.facedown_score += s.score

    def play_turn(self, active_card=None, drawn=False, return_set=False):
        """Models the player turn, returns a card to discard.  Returns draw if
        no sets can be melded - this is so that game.py knows to deal another card.
        Returns kaeu (the customary winning call) if, after a meld, the player can win.
        Here the player only melds if doing so results in a higher score.
        Returns the melded set if the return_set flag is set to true.
        The player can now Tok given that they have at least one lang pai to discard.
        This implementation is a simple rules-based AI based on observations of typical gameplay"""
        #Evaluate the hand combined with the active card
        old_hand=[c for c in self.hand]
        h=[c for c in self.hand]
        h.append(active_card)
        fs, hs, lp = evaluate_hand(h,return_sets=True)
        ms = None
        #MELD CRITERIA
        if hs > self.hand_score or self.can_tok(hs,lp):
            #Look for the melded set
            for s in fs:
                if s.melded:
                    self.melded_sets.append(s)
                    self.melded_score += s.score
                    for c in s.cards: h.remove(c)
                    ms = s
            #Update the player's hand
            self.hand = h
            self.evaluate_player_hand()
            #Assess winning condition
            if self.can_win():
                if return_set: return ms, 'kaeu'
                return 'kaeu'
            #Choose a card to discard
            else:
                dc = self.discard_card()
                #Revert player hand if the player cannot discard
                if dc==None:
                    self.melded_sets.remove(ms)
                    self.melded_score -= ms.score
                    self.hand=old_hand
                    self.evaluate_player_hand()
                    #Discard the active card / draw from the deck
                    if drawn:
                        if return_set: return None, active_card
                        return active_card
                    else:
                        if return_set: return None, 'draw'
                        return 'draw'
                dc.active=True #activate the discarded card
                if return_set: return ms, dc
                return dc
        elif drawn:
            #If the player can't meld with a drawn card, they must discard it
            if return_set: return ms, active_card
            return active_card
        else:
            #Return draw so game.py knows to provide another card
            if return_set: return None, 'draw'
            return 'draw'

    def check_meld(self, active_card):
        """Returns the set that the player can meld with the given active card,
        or none if no such set exists.  Note this does NOT make any changes to
        the player hand and/or score."""
        h=[c for c in self.hand]
        h.append(active_card)
        fs, hs, lp = evaluate_hand(h,return_sets=True)
        ms = None
        for s in fs:
            if s.melded: ms=s; break
        #If there is no such melded set then return None right away
        if ms==None: return None
        #Otherwise we need to ensure that the player can discard
        #and that the meld actually increases the player's hand score
        fs.remove(ms)
        if (len(lp) > 0 or exists_nks(fs)) and hs > self.hand_score: return ms
        return None

    def update_scores(self):
        """Test function - Refreshes all score variables"""
        self.hand_score = self.melded_score = self.facedown_score = self.total_score = 0
        hs, lp = evaluate_hand(self.hand)
        self.hand_score = hs
        for s in self.facedown_sets: self.facedown_score += s.score
        for s in self.melded_sets: self.melded_score += s.score
        self.total_score = self.hand_score + self.facedown_score + self.melded_score

    def update_collection(self):
        """Test function - Rebuilds and re-sorts the list of all player cards"""
        self.collection=[]
        for c in self.hand: c.locked=False; self.collection.append(c)
        for s in self.facedown_sets:
            for c in s.cards: self.collection.append(c)
        for s in self.melded_sets:
            for c in s.cards: self.collection.append(c)
        self.collection=sort_cards(self.collection)

    def evaluate_player_hand(self):
        """Evaluates the sets in the player's hand.  This should be called after
        removing any facedown and melded sets.  Also calls update_collection()"""
        fs, hs, lp = evaluate_hand(self.hand,return_sets=True)
        self.hand_sets = fs
        self.hand_score = hs
        self.lang_pai = lp
        self.total_score = self.hand_score + self.facedown_score + self.melded_score
        self.update_collection()

    def can_win(self):
        """Test for the winning criteria"""
        return len(self.lang_pai) == 0 and self.total_score >= 9

    def can_tok(self,hs,lp):
        """Test for being able to perform the special TOK move"""
        return (hs==self.hand_score and len(lp) < len(self.lang_pai)
        and len(self.lang_pai) > 0 and self.total_score >= 9)

    def discard_card(self):
        """Discards a random lang pai, or breaks up a pair/chut if there are
        no lang pai"""
        if len(self.lang_pai) > 0:
            #use [0] to extract the object rather than the numpy array
            dc = np.random.choice(self.lang_pai,1)[0]
            self.hand.remove(dc)
            self.evaluate_player_hand() #update player hand
            return dc
        elif not self.can_win():
            #We need to first determine if there are any non-Kuin sets to break up
            #If not, then we cannot discard anything (Kuin cannot be discarded)
            nks=exists_nks(self.hand_sets)
            if not nks: return None
            #Attempt to break a pair
            for s in self.hand_sets:
                if len(s.cards) == 2:
                    dc = np.random.choice(s.cards,1)[0]
                    self.hand.remove(dc)
                    self.evaluate_player_hand() #update player hand
                    return dc
            #Otherwise break a 3-colour chut (as this set has the highest probability
            #of being able to be melded again later)
            for s in self.hand_sets:
                if len(s.cards) == 3 and cards_all_suit(s.cards,suit='chut'):
                    dc = np.random.choice(s.cards,1)[0]
                    self.hand.remove(dc)
                    self.evaluate_player_hand() #update player hand
                    return dc
            #Otherwise break a random non-Kuin set with the lowest score
            ms = 10 #some impossibly high number
            for s in self.hand_sets:
                if len(s.cards) > 1 and s.score < ms: ms = s.score
            rs = np.random.choice(self.hand_sets,1)[0]
            #Now choose a random non-Kuin set with this minimum score
            while len(rs.cards) == 1 or rs.score != ms:
                rs = np.random.choice(self.hand_sets,1)[0]
            dc = np.random.choice(rs.cards,1)[0]
            self.hand.remove(dc)
            self.evaluate_player_hand()
            return dc
        else:
            return None

    def update_field_info(self,dcards,msets):
        """Update information about the field of player"""
        self.field_discards=[dc for dc in dcards]
        self.field_melded_sets=[ms for ms in msets]

    def print_hand(self): print(self.hand)

    def info(self):
        return "Player %s with score %d" % (self.name, self.total_score)

    def __repr__(self):
        return "%s" % self.name

#=============================================================================#
#GENERAL FUNCTIONS
#=============================================================================#

def cards_same_colour(cards):
    """Determines if all cards are of the same colour"""
    test_colour=cards[0].colour
    for i in cards:
        if i.colour != test_colour: return False
    return True

def cards_same_suit(cards):
    """Determines if all cards are of the same suit"""
    test_suit=cards[0].suit
    for i in cards:
        if i.suit != test_suit: return False
    return True

def cards_unique_colours(cards):
    """Determines if each card is of a unique colour"""
    for i in cards:
        test_colour=i.colour
        for j in cards:
            if i == j: continue
            if j.colour == test_colour: return False
    return True

def cards_all_suit(cards, suit):
    """Determines if all the cards are of a given suit"""
    for i in cards:
        if i.suit != suit: return False
    return True

def cards_not_in(cards, card_list):
    """Determines if each card in a list of cards does not appear in another list"""
    for i in cards:
        if i in card_list: return False
    return True

def cards_not_locked(cards):
    """Determines if all the cards in a given list are unlocked"""
    for i in cards:
        if i.locked: return False
    return True

def contains_active_card(cards):
    """Determines if the active card is part of the given list of cards"""
    for i in cards:
        if i.active: return True
    return False

def is_identical_set(set):
    """Determines if the given set is an identical set"""
    return cards_same_suit(set.cards) and cards_same_colour(set.cards)

def is_four_colour_set(set):
    """Determines if the given set is a 4-colour set"""
    return (cards_same_suit(set.cards) and cards_unique_colours(set.cards)
    and len(set.cards)==4 and set.cards[0].suit=='chut')

def sort_cards(cards, by='suit'):
    """Sorts cards either by suit or by colour"""
    cards.sort(key=lambda x: x.rank)
    if by=='colour':
        sorted_cards=[]
        for i in cards[0].validColours:
            for j in cards:
                if j.colour == i: sorted_cards.append(j)
    else: sorted_cards=cards
    return sorted_cards

def exists_identical_set(sets,size=3,suit='',colour='all'):
    """Determines if there exists the described identical set in a given list of sets."""
    for s in sets:
        if len(s.cards) != size: continue
        test_colour=s.cards[0].colour
        set_found=True
        for c in s.cards:
            if colour=='all': #i.e just check for an arbitrary colour
                if c.suit != suit or c.colour != test_colour: set_found = False
            elif c.suit != suit or c.colour != colour: set_found = False
        if set_found: return True #only need to know if one such set exists
    return False

def hand_contains_suit(hand,suit):
    """Determines if there exists at least one card of the given suit in the player's hand"""
    for c in hand:
        if c.suit == suit: return True
    return False

def exists_nks(hand_sets):
    """Determines if there exists a non-kuin set in a given list of sets
    that can be broken up so as to be used for discards, etc"""
    for s in hand_sets:
        if len(s.cards) > 1: return True
    return False

def evaluate_hand(hand_cards, return_sets=False):
    """Determines the combined score of all sets from the given list of cards.
    Returns a list of found sets (optional), the hand score and a list of lang pai"""

    cards=sort_cards(hand_cards) #Just in case the given cards are not yet sorted
    hand_score=0
    found_sets=[]
    lang_pai=[] #Loose cards that do not form sets
    valid_multicolour_suits=['chut']

    i=0
    #First we look for 4-card identical sets, performing a simple linear search
    while i <= len(cards)-4:
        #Note that we can simply use valid_scores as a way to check if the sets
        #correspond to identical cards as ONLY 4-of-a-kind sets can have these values.
        valid_scores=[8,6]
        test_cards=cards[i:i+4]
        test_set=Set(test_cards)
        if test_set.score in valid_scores and cards_not_locked(test_cards):
            found_sets.append(test_set)
            for c in test_cards: c.lock()
            i += 3
        i += 1

    #Now we look for 4-card multicolour sets.  This requires a quadruple loop
    #This also solves the Green Chut cases of the form
    #[red chut, yellow chut, white chut, green chut, green chut, green chut, green chut]
    #since 4-of-a-kinds are now checked first, THEN followed by 4-colour chut.
    for i in range(len(cards)):
        if cards[i].suit not in valid_multicolour_suits: continue
        #It is assumed that, if i is chut, then j,k,l will also all be chut
        for j in range(i+1,len(cards)):
            for k in range(j+1,len(cards)):
                for l in range(k+1,len(cards)):
                    test_cards=[cards[i],cards[j],cards[k],cards[l]]
                    test_set=Set(test_cards)
                    if test_set.score == 4 and cards_not_locked(test_cards):
                        found_sets.append(test_set)
                        for c in test_cards: c.lock()

    i=0
    #Now we look for 3-card identical sets (specifically exclude consecutive + multicolour sets)
    while i <= len(cards)-3:
        valid_scores=[3,1] #valid scores for 3-card identical sets
        test_cards=cards[i:i+3]
        #Need to ensure that the cards are actually identical
        #This fixes cases like [kee mah pao pao pao] where the kee mah pao incorrectly takes precedence
        if cards_same_suit(test_cards) and cards_same_colour(test_cards):
            test_set=Set(test_cards)
            if test_set.score in valid_scores and cards_not_locked(test_cards):
                found_sets.append(test_set)
                for c in test_cards: c.lock()
                i += 2
        i += 1

    #Now we look for 3-card consecutive and other multicolour sets
    for i in range(len(cards)):
        for j in range(i+1,len(cards)):
            for k in range(j+1,len(cards)):
                #Look for both kuin-tse-xiong, kee-mah-pau and 3-colour-chut
                valid_scores=[2,1]
                test_cards=[cards[i],cards[j],cards[k]]
                test_set=Set(test_cards)
                if test_set.score in valid_scores and cards_not_locked(test_cards):
                    found_sets.append(test_set)
                    for c in test_cards: c.lock()

    #Now we check for standalone Kuin
    for i in cards:
        if i.suit=='kuin' and not i.locked:
            found_sets.append(Set([i])) #Set takes a list of cards!
            i.lock()

    i=0
    #Finally, check for pairs
    while i <= len(cards)-2:
        test_cards=cards[i:i+2]
        test_set=Set(test_cards)
        if test_set.score == 0 and cards_not_locked(test_cards):
            found_sets.append(test_set)
            for c in test_cards: c.lock()
        i += 1

    #Now determine the hand score
    for s in found_sets: hand_score += s.score

    #And finally determine the lang pai (note pairs are not lang pai)
    for c in cards:
        if not c.locked: lang_pai.append(c)

    #Unlock the cards so that they can be checked again
    for c in cards: c.locked=False

    if return_sets: return found_sets, hand_score, lang_pai
    return hand_score, lang_pai

if __name__ == '__main__':
    d=Deck()
    th=sort_cards(d.draw_cards(21))
    print('\nYou have been dealt the following cards:\n')
    print(th)
    fs, hs, lp = evaluate_hand(th, return_sets=True)
    print('\nYour hand is worth',hs,'points\n')
    for i in fs: print(i)
