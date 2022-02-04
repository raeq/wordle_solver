from string import ascii_letters
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
        if value.result == Result.NOTPRESENT:
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
    # first sort these according to word frquency

    intersection: list = [word for word in common_words if word in possible_words]
    my_len = len(intersection)

    if my_len < size:
        for word in possible_words:
            if word not in intersection:
                intersection.append(word)
            if len(intersection) >= size:
                break

    # take each position and see the count of letters in that position

    from collections import Counter
    letters = []

    for i in range(5):
        letters.append([])

    for word in intersection:
        for i in range(5):
            letters[i].append(word[i])

    for i in range(5):
        letters[i] = Counter(letters[i])

    bests = []
    for i in range(len(letters)):
        c = Counter(letters[i])
        bests.append((i, c.most_common(1)[0]))
    print(bests)

    return intersection[0:size]


def calculate_frequency_score(word: str) -> float:
    return sum([frequencies.frequencies[letter.upper()] for letter in word if
                len(set(word)) == 5])


def evaluate(guess: str, correct: str) -> list[Guess]:
    result = []
    for index, letter in enumerate(guess):
        if correct[index] == letter:
            result.append(Guess(letter=letter, result=Result.CORRECT_LOCATION))
        elif letter not in correct:
            result.append(Guess(letter=letter, result=Result.NOTPRESENT))
        else:
            result.append(Guess(letter=letter, result=Result.INCORRECT_LOCATION))

    return result




def validate_guess(guess: str, all_words:list[str]) -> bool:
    ret_value = False

    if len(guess) == 5:
        if all([x in ascii_letters for x in guess]):
            if guess in all_words:
                ret_value = True

    return ret_value
