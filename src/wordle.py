import cmd

from rich import print

import solve


class WordleSolver(cmd.Cmd):
    intro = \
        """Wordle Solver Copyright (C) 2022 Richard Quinn
        
            This program comes with ABSOLUTELY NO WARRANTY.
            This is free software, and you are welcome to redistribute it
            under certain conditions. See https://www.gnu.org/licenses/gpl-3.0.html.
        
        Type help or ? to list commands."""

    prompt = '(wordle_solver) '
    file = None
    current_wordlist: set[str]
    _all_words: set[str]
    _common_words: list[str]

    @property
    def all_words(self):
        return self._all_words

    @property
    def common_words(self):
        return self._common_words

    def __init__(self, all_words: set[str], common_words: list[str]) -> None:
        self._all_words = all_words
        self._common_words = common_words
        self.current_wordlist = all_words
        super().__init__()

    def do_reversesolve(self, arg1):
        """Enter the solution and the program will tell you the optimum starting
        guess(es)."""
        if solve.validate_guess(guess=arg1, all_words=self.all_words):
            print(solve.best_starting_word(
                word_list=self.all_words, target=arg1))

    def do_search(self, arg1):
        q, l = arg1.split(" ")
        q = int(q)
        print(solve.search(self.current_wordlist, letter=l, quantity=q))

    def do_reset(self, arg1):
        self.current_wordlist = self.all_words
        print(f"Game eas reset, using {len(self.all_words)} words.")

    def do_solve(self, arg1):
        self.current_wordlist = self.all_words

        g, c = arg1.split(" ")
        if not solve.validate_guess(g, self.all_words):
            print(f"Invalid guess, '{g}' not in dictionary.")
            return
        if not solve.validate_guess(c, self.all_words):
            print(f"Invalid guess, '{c}' not in dictionary.")
            return

        n: int = 0

        while True:
            guess_list = solve.evaluate(g, c)
            guess_input = "".join([x.result.value for x in guess_list])

            guess, word = solve.parse_input(g + " " + guess_input)

            print(f"Your guess is '{g}', result is '{guess_input}'.")

            self.current_wordlist = solve.get_top_recommendations(self.current_wordlist, guess)
            top_suggestions = solve.top_choices2(self.common_words, self.current_wordlist, 100)

            g = top_suggestions[0]

            n += 1
            if n >= 6 or guess_input == "=====":
                break

    def do_evaluate(self, arg1):
        g, c = arg1.split(" ")
        if not solve.validate_guess(g, self.all_words):
            print(f"Invalid guess, '{g}' not in dictionary.")
            return
        if not solve.validate_guess(c, self.all_words):
            print(f"Invalid guess, '{c}' not in dictionary.")
            return

        print(solve.evaluate(guess=g, correct=c))

    def do_guess(self, arg1):
        guess, word = solve.parse_input(arg1)

        if not solve.validate_guess(word, self.all_words):
            print(f"Invalid guess, '{word}' not in dictionary.")
            return

        print("You guessed: ", "".join([l for l, r in guess]))

        self.current_wordlist = solve.get_top_recommendations(self.current_wordlist, guess)
        top_suggestions = solve.top_choices(self.common_words, self.current_wordlist, 40)

        print(f"Top choices of {len(self.current_wordlist)}: "
              f"{top_suggestions}")

    def do_bye(self, arg1):
        """Stop recording, close the  window, and exit:  BYE"""
        print('Thank you.')
        return True

    # ----- record and playback -----
    def do_record(self, arg):
        """Save future commands to filename:  RECORD rose.cmd"""
        self.file = open(arg, 'w')

    def do_playback(self, arg):
        """Playback commands from a file:  PLAYBACK rose.cmd"""
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
    common_w: list[str] = solve.filter_length(solve.load_common_words(), 5)
    all_w: set[str] = solve.load_all_words()

    WordleSolver(all_words=all_w, common_words=common_w).cmdloop()
