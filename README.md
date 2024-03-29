# sisepai
Python 3.X code for the Chinese card game Sisepai (Four Colour Cards) (21 card variant)
***
**NOTE `numpy` is required!**

Simply execute the code in a terminal:

```$ python3 game.py```

You can also run `game.py` as an executable (ensure you have sufficient permissions by first running `chmod +x game.py`)

Examples of possible simulations:
- `play_game()` - default 4-player game
- `play_game(8)` - 8-player game
- `play_game(8,nturns=50)` - simulate an 8-player game for 50 turns
- `play_game(8,is_verbose=False)` - disable verbose logging (helpful when simulating millions of games)
- `play_game(8,with_oot=False)` - disable out-of-turn melding

### Rationale

Sisepai is a rummy-like card game that originated in southern China.  As I am half-Chinese, and hearing how the game is in decline,
this personal project is an attempt to record the essence of the game (as it is known to my family) in both code and a brief rulebook.
My family plays two variants that I have called 21-card and 26-card Sisepai (in order to distinguish it from the other types that exist).
Unfortunately, as is often the case with games passed down orally, the rules of the game are seldom recorded, and regional variations
have effectively led to a family of Sisepai-style games rather than a single standard.  For example, the [Wikipedia article](https://en.wikipedia.org/wiki/Four_Color_Cards)
on the topic appears to describe the 26-card game, while [this](https://www.cs.cmu.edu/~tnt/rules.html) site describes the 21-card game
with different terminology.  In both this implementation and the attached PDF guide, the names of the cards are how they are pronounced in
Hakka Chinese (the language my family speak), and the terminology is a mix of terms that I have coined as well as conventions
used by my family.

### Code Structure

The code is a simple implementation of the game logic using a rules-based agent.  `sisepai.py` contains all the necessary classes
and functions to model the game objects (Cards, Sets, Decks, Players), while `game.py` contains the core game logic.
The files require `numpy` to run.

### Possible Extensions

- Create new Player agents to compare and constrast strategies
- Adapt the existing 21-card game code into a version for the 26-card game.
- Introduce a human player either through interaction in the terminal or a GUI
