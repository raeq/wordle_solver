from enum import Enum
from typing import NamedTuple

import frequencies


class Result(Enum):
    NOTPRESENT = "-"
    INCORRECT_LOCATION = "+"
    CORRECT_LOCATION = "="


class Guess(NamedTuple):
    letter: str
    result: Result


def parse_input(user_input: str) -> list[Guess]:
    word, results = user_input.split(" ")
    parsed_input = []

    for l, r in zip(word, results):
        g = Guess(letter=l.lower(),
                  result=Result(r))
        parsed_input.append(g)

    return parsed_input


def get_top_recommendations(words: set[str], guess: list[Guess]):
    words = set(words)
    # only keep words which have this letter in this position
    for key, value in enumerate(guess):
        if value.result == Result.CORRECT_LOCATION:
            words = {word for word in words if word[key] == value.letter}

    # only keep words which have this letter somewhere
    for key, value in enumerate(guess):
        if value.result == Result.INCORRECT_LOCATION:
            words = {word for word in words if word[key] != value.letter and value.letter in word}

    # only keep words which do not have this letter
    for key, value in enumerate(guess):
        if value.result == Result.NOTPRESENT:
            words = {word for word in words if value.letter not in word}

    ranked_words = {(word, calculate_frequency_score(word)) for word in words}
    ranked_words = sorted(ranked_words, key=lambda x: x[1], reverse=True)
    return [word for word, score in ranked_words]


def calculate_frequency_score(word: str) -> float:
    return sum([frequencies.frequencies[letter.upper()] for letter in word if
                len(set(word)) == 5])
