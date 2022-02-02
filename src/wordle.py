import cmd
from rich import print
import solve


class WordleSolver(cmd.Cmd):
    intro = \
"""Wordle Solver Copyright (C) 2022 Richard Quinn

    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions. See http://www.gnu.org/licenses/gpl-3.0.html.

Type help or ? to list commands."""

    prompt = '(wordle_solver) '
    file = None
    current_wordlist: list[str] = []

    def __init__(self, words:list[str]):
        self.current_wordlist = words
        super().__init__()

    def do_newgame(self):
        print("You are starting a new game.")

    def do_guess(self, arg1):
        guess: list[solve.Guess] = solve.parse_input(arg1)

        print("You guessed: ", "".join([l for l, r in guess]))

        self.current_wordlist = solve.get_top_recommendations(self.current_wordlist, guess)
        print(f"Top choices: {self.current_wordlist[0:10]}")


    def do_bye(self, arg):
        'Stop recording, close the  window, and exit:  BYE'
        print('Thank you.')
        return True

    # ----- record and playback -----
    def do_record(self, arg):
        'Save future commands to filename:  RECORD rose.cmd'
        self.file = open(arg, 'w')

    def do_playback(self, arg):
        'Playback commands from a file:  PLAYBACK rose.cmd'
        self.close()
        with open(arg) as f:
            self.cmdqueue.extend(f.read().splitlines())

    def precmd(self, line):
        line = line.lower()
        if self.file and 'playback' not in line:
            print(line, file=self.file)
        return line

    def close(self):
        if self.file:
            self.file.close()
            self.file = None


if __name__ == '__main__':
    all_words: list[str] = sorted([line.rstrip() for line in open("words.txt").readlines()])
    new_words: list[str] = all_words.copy()

    WordleSolver(words=all_words).cmdloop()