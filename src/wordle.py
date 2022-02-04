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
    current_wordlist: set[str] = []

    def __init__(self, words: set[str]):
        self.current_wordlist = words
        super().__init__()

    def do_newgame(self):
        print("You are starting a new game.")

    def do_guess(self, arg1):
        guess: list[solve.Guess] = solve.parse_input(arg1)

        print("You guessed: ", "".join([l for l, r in guess]))

        self.current_wordlist = solve.get_top_recommendations(self.current_wordlist, guess)
        print(f"Top choices of {len(self.current_wordlist)}: {top_choices(common_words, self.current_wordlist, 10)}")


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


def top_choices(common_words: list[str], possible_words: set[str], size: int = 10) -> list[str]:
    intersection: list = [word for word in common_words if word in possible_words]
    my_len = len(intersection)

    if my_len < size:
        for word in possible_words:
            if word not in intersection and word in all_words:
                intersection.append(word)
            if len(intersection) >= size:
                break

    return intersection[0:size]


if __name__ == '__main__':
    common_words = [line.rstrip().split(" ")[-1] for line in open("common_words.txt").readlines()]
    common_words = [word for word in common_words if len(word) == 5]
    all_words: set[str] = {line.rstrip() for line in open("words.txt").readlines()}
    new_words: set[str] = all_words.copy()

    WordleSolver(words=all_words).cmdloop()
