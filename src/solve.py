from enum import Enum
from string import ascii_letters
from typing import NamedTuple, Sequence

import frequencies


class Result(Enum):
    NOT_PRESENT = "-"
    INCORRECT_LOCATION = "+"
    CORRECT_LOCATION = "="


class Guess(NamedTuple):
    letter: str
    result: Result


def parse_input(user_input: str) -> tuple[list[Guess], str]:
    word, results = user_input.split(" ")
    parsed_input = []

    for l, r in zip(word, results):
        g = Guess(letter=l.lower(),
                  result=Result(r))
        parsed_input.append(g)

    return parsed_input, "".join([l for l, r in parsed_input])


def get_top_recommendations(words: set[str], guess: list[Guess]):
    words = set(words)
    word = "".join([_.letter for _ in guess])

    # only keep words which have this letter in this position
    for key, value in enumerate(guess):
        if value.result == Result.CORRECT_LOCATION:
            words = {word for word in words if word[key] == value.letter}

    # only keep words which do not have this letter
    for key, value in enumerate(guess):
        if value.result == Result.NOT_PRESENT:
            if word.count(value.letter) == 1:
                words = {word for word in words if value.letter not in word}
            else:
                words = {word for word in words if word[key] != value.letter}

    # only keep words which have this letter somewhere
    for key, value in enumerate(guess):
        if value.result == Result.INCORRECT_LOCATION:
            words = {word for word in words if value.letter in word and word[key] != value.letter}

    ranked_words = {(word, calculate_frequency_score(word)) for word in words}
    ranked_words = sorted(ranked_words, key=lambda x: x[1], reverse=True)
    return [word for word, score in ranked_words]


def top_choices(common_words: list[str], possible_words: set[str], size: int = 10) -> list[str]:
    # first sort these according to word frequency

    intersection: list = [word for word in common_words if word in possible_words]
    my_len = len(intersection)

    if my_len < size:
        for word in possible_words:
            if word not in intersection:
                intersection.append(word)
            if len(intersection) >= size:
                break

    return intersection[:size]

    # take each position and see the count of letters in that position


def top_choices2(common_words: list[str], possible_words: set[str], size: int = 10) -> list[str]:
    from collections import Counter
    intersection: list = [word for word in common_words if word in possible_words]

    letters = []

    for i in range(5):
        letters.append([])

    for word in intersection:
        for index, letter in enumerate(word):
            letters[index].append(letter)

    for i in range(5):
        letters[i] = Counter(letters[i])

    bests = []
    for index, data in enumerate(letters):
        c = Counter(data)
        bests.append(c.most_common(1)[0])

    standard_choice = intersection[0]
    better_choices = intersection.copy()

    for index, most_common in enumerate(bests):
        if most_common[0] != standard_choice[index]:
            # see if we can choose a better word
            temp = [word for word in better_choices if word[index] == most_common[0]]
            if len(temp) > 0:
                better_choices = temp

    return better_choices[0:size]


def calculate_frequency_score(word: str) -> float:
    return sum([frequencies.frequencies[letter.upper()] for letter in word if
                len(set(word)) == 5])


def evaluate(guess: str, correct: str) -> list[Guess]:
    result = []
    for index, letter in enumerate(guess):
        if correct[index] == letter:
            result.append(Guess(letter=letter, result=Result.CORRECT_LOCATION))
        elif letter not in correct:
            result.append(Guess(letter=letter, result=Result.NOT_PRESENT))
        else:
            result.append(Guess(letter=letter, result=Result.INCORRECT_LOCATION))

    return result


def validate_guess(guess: str, all_words: set[str]) -> bool:
    ret_value = False

    if len(guess) == 5:
        if all([x in ascii_letters for x in guess]):
            if guess in all_words:
                ret_value = True

    return ret_value


def search(word_list: set[str], letter: str, quantity: int = 1) -> set[str]:
    return {word for word in word_list if word.count(letter) == quantity}


def best_starting_word(word_list: set[str], target: str) -> list[str]:
    results: list[tuple[int, str]] = []

    for idx, g in enumerate(word_list):
        original_g = g + ""
        n: int = 0
        current_wordlist = word_list.copy()

        while True:
            guess_list = evaluate(g, target)
            guess_input = "".join([x.result.value for x in guess_list])

            guess, word = parse_input(g + " " + guess_input)

            current_wordlist = get_top_recommendations(current_wordlist, guess)

            g = current_wordlist[0]

            n += 1
            if n >= 6 or guess_input == "=====":
                print(f"Found {len(results)} of {idx} attempts.", end='\r', flush=True)

                if n < 3:
                    results.append((n, original_g))
                break

    return [word for counter, word in results if counter < 3]


def load_all_words(filename: str = "words.txt") -> set[str]:
    return {line.rstrip().lower() for line in open(filename).readlines()}


def load_common_words(filename: str = "common_words.txt") -> list[str]:
    return [word for word in [line.rstrip().split(" ")[-1].lower()
                              for line in open(filename).readlines()]]


def filter_length(words: Sequence, length: int = 5) -> list[str]:
    return list(filter(lambda x: len(x) == length, words))
