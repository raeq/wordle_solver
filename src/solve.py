from enum import Enum
from typing import List, Set, Tuple, NamedTuple
from dataclasses import dataclass
from functools import lru_cache
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SolverError(Exception):
    """Custom exception for solver errors"""
    pass

class Result(Enum):
    """Enum representing the result of a letter guess in Wordle"""
    NOTPRESENT = "b"  # Black/Gray - letter not in word
    INCORRECT_LOCATION = "y"  # Yellow - letter in word but wrong position  
    CORRECT_LOCATION = "g"  # Green - letter in correct position

@dataclass(frozen=True)
class Guess:
    """Represents a single letter guess and its result"""
    letter: str
    result: Result
    
    def __post_init__(self):
        if not isinstance(self.letter, str) or len(self.letter) != 1:
            raise ValueError("Letter must be a single character")
        if not self.letter.isalpha():
            raise ValueError("Letter must be alphabetic")


import frequencies


class Guess(NamedTuple):
    letter: str
    result: Result


def parse_input(input_str: str) -> List[Guess]:
    """Parse input string into list of Guess objects
    
    Args:
        input_str: String like "arose gybgy" (word + color pattern)
        
    Returns:
        List of Guess objects
        
    Raises:
        ValueError: If input format is invalid
    """
    if not input_str or not input_str.strip():
        raise ValueError("Input cannot be empty")
    
    parts = input_str.strip().split()
    if len(parts) != 2:
        raise ValueError("Input must contain exactly one word and one color pattern")
    
    word, colors = parts
    word = word.lower()
    colors = colors.lower()
    
    if len(word) != 5 or len(colors) != 5:
        raise ValueError("Both word and color pattern must be exactly 5 characters")
    
    if not word.isalpha():
        raise ValueError("Word must contain only letters")
    
    valid_colors = {'g', 'y', 'b'}
    if not all(c in valid_colors for c in colors):
        raise ValueError("Color pattern must only contain 'g', 'y', 'b'")
    
    color_map = {'g': Result.CORRECT_LOCATION, 'y': Result.INCORRECT_LOCATION, 'b': Result.NOTPRESENT}
    
    return [Guess(letter=letter, result=color_map[color]) 
            for letter, color in zip(word, colors)]


def get_top_recommendations(possible_words: Set[str], guesses: List[Guess]) -> Set[str]:
    """Filter possible words based on guess results
    
    Args:
        possible_words: Set of currently possible words
        guesses: List of letter guesses with results
        
    Returns:
        Filtered set of possible words
    """
    if not guesses:
        return possible_words
    
    filtered_words = set()
    
    for word in possible_words:
        if _word_matches_guesses(word, guesses):
            filtered_words.add(word)
    
    return filtered_words

def _word_matches_guesses(word: str, guesses: List[Guess]) -> bool:
    """Check if a word matches all the given guesses"""
    word = word.lower()
    
    # Track letter counts in the word
    word_letter_counts = {}
    for letter in word:
        word_letter_counts[letter] = word_letter_counts.get(letter, 0) + 1
    
    # First pass: handle green (correct position) letters
    green_positions = {}
    for i, guess in enumerate(guesses):
        if guess.result == Result.CORRECT_LOCATION:
            if word[i] != guess.letter:
                return False
            green_positions[i] = guess.letter
            word_letter_counts[guess.letter] -= 1
    
    # Second pass: handle yellow and black letters
    yellow_letters = set()
    black_letters = set()
    
    for i, guess in enumerate(guesses):
        if guess.result == Result.INCORRECT_LOCATION:
            # Letter must be in word but not at this position
            if word[i] == guess.letter:
                return False
            if word_letter_counts.get(guess.letter, 0) <= 0:
                return False
            yellow_letters.add(guess.letter)
            word_letter_counts[guess.letter] -= 1
            
        elif guess.result == Result.NOTPRESENT:
            # Letter should not appear in word (except where it's green)
            remaining_count = word_letter_counts.get(guess.letter, 0)
            if remaining_count > 0:
                return False
            black_letters.add(guess.letter)
    
    return True


def calculate_frequency_score(word: str) -> float:
    return sum([frequencies.frequencies[letter.upper()] for letter in word if
                len(set(word)) == 5])

import json
from pathlib import Path
from typing import Dict

class FrequencyAnalyzer:
    """Analyzes letter and position frequencies for better word recommendations"""
    
    def __init__(self, words: Set[str]):
        self.words = words
        self._letter_frequencies = self._calculate_letter_frequencies()
        self._position_frequencies = self._calculate_position_frequencies()
        self._letter_pair_frequencies = self._calculate_pair_frequencies()
    
    def _calculate_letter_frequencies(self) -> Dict[str, float]:
        """Calculate frequency of each letter across all words"""
        letter_counts = {}
        total_letters = 0
        
        for word in self.words:
            for letter in set(word):  # Count each letter once per word
                letter_counts[letter] = letter_counts.get(letter, 0) + 1
                total_letters += 1
        
        return {letter: count / total_letters for letter, count in letter_counts.items()}
    
    def _calculate_position_frequencies(self) -> Dict[Tuple[str, int], float]:
        """Calculate frequency of letters at specific positions"""
        position_counts = {}
        total_words = len(self.words)
        
        for word in self.words:
            for pos, letter in enumerate(word):
                key = (letter, pos)
                position_counts[key] = position_counts.get(key, 0) + 1
        
        return {key: count / total_words for key, count in position_counts.items()}
    
    def _calculate_pair_frequencies(self) -> Dict[str, float]:
        """Calculate frequency of letter pairs"""
        pair_counts = {}
        total_pairs = 0
        
        for word in self.words:
            for i in range(len(word) - 1):
                pair = word[i:i+2]
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
                total_pairs += 1
        
        return {pair: count / total_pairs for pair, count in pair_counts.items()}
    
    def calculate_word_score(self, word: str) -> float:
        """Calculate a comprehensive score for a word"""
        word = word.lower()
        
        # Letter frequency score
        letter_score = sum(self._letter_frequencies.get(letter, 0) for letter in set(word))
        
        # Position frequency score
        position_score = sum(
            self._position_frequencies.get((letter, pos), 0) 
            for pos, letter in enumerate(word)
        )
        
        # Letter pair score
        pair_score = sum(
            self._letter_pair_frequencies.get(word[i:i+2], 0) 
            for i in range(len(word) - 1)
        )
        
        # Unique letter bonus (words with more unique letters are generally better)
        unique_bonus = len(set(word)) / 5.0
        
        return letter_score * 0.3 + position_score * 0.4 + pair_score * 0.2 + unique_bonus * 0.1

def get_best_recommendations(possible_words: Set[str], count: int = 10) -> List[str]:
    """Get the best word recommendations based on frequency analysis"""
    if not possible_words:
        return []
    
    analyzer = FrequencyAnalyzer(possible_words)
    
    # Score all words
    scored_words = [
        (word, analyzer.calculate_word_score(word)) 
        for word in possible_words
    ]
    
    # Sort by score (highest first)
    scored_words.sort(key=lambda x: x[1], reverse=True)
    
    return [word for word, _ in scored_words[:count]]

class WordleSolver:
    """Main solver class with caching and optimization"""
    
    def __init__(self, word_set: Set[str]):
        self.all_words = word_set
        self.analyzer = FrequencyAnalyzer(word_set)
        self._cache = {}
    
    @lru_cache(maxsize=1000)
    def filter_words(self, possible_words_tuple: Tuple[str, ...], guesses_str: str) -> Tuple[str, ...]:
        """Cached word filtering for better performance"""
        possible_words = set(possible_words_tuple)
        guesses = parse_input(guesses_str)
        filtered = get_top_recommendations(possible_words, guesses)
        return tuple(sorted(filtered))
    
    def solve_step(self, current_words: Set[str], guess_input: str) -> Tuple[Set[str], List[str], float]:
        """Perform one solve step and return results with timing"""
        start_time = time.time()
        
        # Filter words based on guess
        guesses = parse_input(guess_input)
        filtered_words = get_top_recommendations(current_words, guesses)
        
        # Get best recommendations
        recommendations = get_best_recommendations(filtered_words, 10)
        
        solve_time = time.time() - start_time
        
        return filtered_words, recommendations, solve_time
    
    def get_optimal_first_guess(self) -> str:
        """Calculate the optimal first guess"""
        # Common optimal starting words based on frequency analysis
        candidates = ['arose', 'slate', 'crane', 'trace', 'adieu']
        available_candidates = [word for word in candidates if word in self.all_words]
        
        if available_candidates:
            return available_candidates[0]
        
        # Fall back to frequency analysis
        return get_best_recommendations(self.all_words, 1)[0]

def safe_parse_input(input_str: str) -> Optional[List[Guess]]:
    """Safely parse input with error handling"""
    try:
        return parse_input(input_str)
    except ValueError as e:
        logger.error(f"Failed to parse input '{input_str}': {e}")
        return None

def validate_word_set(words: Set[str]) -> Set[str]:
    """Validate and clean word set"""
    if not words:
        raise SolverError("Word set cannot be empty")
    
    valid_words = set()
    for word in words:
        if isinstance(word, str) and len(word) == 5 and word.isalpha():
            valid_words.add(word.lower())
        else:
            logger.warning(f"Skipping invalid word: {word}")
    
    if not valid_words:
        raise SolverError("No valid 5-letter words found")
    
    return valid_words