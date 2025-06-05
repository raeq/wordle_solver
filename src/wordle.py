import cmd
import logging
from pathlib import Path
from typing import Set, List, Optional, Union
from contextlib import contextmanager
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class SolverConfig:
    """Configuration settings for the Wordle solver"""
    words_file: str = "words.txt"
    common_words_file: str = "common_words.txt"
    max_recommendations: int = 10
    log_level: str = "INFO"
    enable_rich: bool = True
    auto_save_session: bool = False
    session_file: str = "session.json"
    default_first_guess: str = "arose"
    
    @classmethod
    def load_from_file(cls, config_file: str = "config.json") -> 'SolverConfig':
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                return cls(**data)
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()  # Return default config
    
    def save_to_file(self, config_file: str = "config.json") -> None:
        """Save configuration to JSON file"""
        with open(config_file, 'w') as f:
            json.dump(asdict(self), f, indent=2)

try:
    from rich import print
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    print("Rich library not available, falling back to standard print")
    RICH_AVAILABLE = False
    Console = None

try:
    import solve
    SOLVE_MODULE_AVAILABLE = True
except ImportError:
    print("Warning: solve module not available. Some functionality will be limited.")
    SOLVE_MODULE_AVAILABLE = False
    solve = None


class WordleSolverError(Exception):
    """Custom exception for WordleSolver errors"""
    pass


class WordleSolver(cmd.Cmd):
    """Interactive Wordle solver command line interface"""
    
    intro = """Wordle Solver Copyright (C) 2022 Richard Quinn

    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions. See http://www.gnu.org/licenses/gpl-3.0.html.

Type help or ? to list commands."""

    prompt = '(wordle_solver) '
    
    def __init__(self, words_file: str = "words.txt", common_words_file: str = "common_words.txt"):
        """Initialize the Wordle solver
        
        Args:
            words_file: Path to the file containing all valid words
            common_words_file: Path to the file containing common words
        """
        super().__init__()
        self._setup_logging()
        self.file: Optional[object] = None
        self.console = Console() if RICH_AVAILABLE else None
        
        # Initialize word lists
        self.all_words: Set[str] = set()
        self.common_words: List[str] = []
        self.original_wordlist: Set[str] = set()
        self.current_wordlist: Set[str] = set()
        
        # Load word lists
        try:
            self._load_wordlists(words_file, common_words_file)
            self.original_wordlist = self.all_words.copy()
            self.current_wordlist = self.all_words.copy()
        except WordleSolverError as e:
            self._print_error(f"Failed to initialize: {e}")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def _safe_file_open(self, filepath: Union[str, Path], mode: str = 'r'):
        """Context manager for safe file operations"""
        try:
            file_path = Path(filepath)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {filepath}")
            
            with open(file_path, mode, encoding='utf-8') as f:
                yield f
        except Exception as e:
            self.logger.error(f"File operation failed: {e}")
            raise WordleSolverError(f"Cannot access file {filepath}: {e}")
    
    def _load_wordlists(self, words_file: str, common_words_file: str) -> None:
        """Load word lists from files with proper validation"""
        try:
            # Load all words
            with self._safe_file_open(words_file) as f:
                self.all_words = {
                    line.strip().lower() for line in f 
                    if line.strip() and len(line.strip()) == 5 and line.strip().isalpha()
                }
            
            # Load common words
            with self._safe_file_open(common_words_file) as f:
                raw_words = [line.strip().split()[-1].lower() for line in f if line.strip()]
                self.common_words = [
                    word for word in raw_words 
                    if len(word) == 5 and word.isalpha() and word in self.all_words
                ]
            
            if not self.all_words:
                raise WordleSolverError("No valid words loaded")
            
            self.logger.info(f"Loaded {len(self.all_words)} words, {len(self.common_words)} common words")
            
        except Exception as e:
            raise WordleSolverError(f"Failed to load word lists: {e}")
    
    def _print_error(self, message: str) -> None:
        """Print error message with formatting"""
        if RICH_AVAILABLE and self.console:
            self.console.print(f"[red]Error:[/red] {message}")
        else:
            print(f"Error: {message}")
    
    def _print_success(self, message: str) -> None:
        """Print success message with formatting"""
        if RICH_AVAILABLE and self.console:
            self.console.print(f"[green]{message}[/green]")
        else:
            print(message)
    
    def _print_info(self, message: str) -> None:
        """Print info message with formatting"""
        if RICH_AVAILABLE and self.console:
            self.console.print(f"[blue]{message}[/blue]")
        else:
            print(message)
    
    def do_newgame(self, arg: str) -> None:
        """Start a new Wordle game by resetting the wordlist: NEWGAME"""
        if arg:
            self._print_error("NEWGAME command takes no arguments")
            return
        
        self.current_wordlist = self.original_wordlist.copy()
        self._print_success("Starting a new game.")
        self._print_info(f"Ready to play! {len(self.current_wordlist)} possible words.")
    
    def do_guess(self, arg: str) -> None:
        """Process a guess and update possible words: GUESS <word><colors>
        
        Example: GUESS arose gybgy (g=green, y=yellow, b=black/gray)
        """
        if not arg.strip():
            self._print_error("Please provide a guess. Type 'help guess' for format.")
            return
        
        if not SOLVE_MODULE_AVAILABLE:
            self._print_error("Solve module not available. Cannot process guesses.")
            return
        
        try:
            guess = solve.parse_input(arg)
            word = "".join([letter for letter, _ in guess])
            
            self._print_info(f"You guessed: {word}")
            
            self.current_wordlist = solve.get_top_recommendations(self.current_wordlist, guess)
            top_words = self._get_top_choices(self.current_wordlist, 10)
            
            self._display_recommendations(top_words)
            
        except Exception as e:
            self._print_error(f"Failed to process guess: {e}")
    
    def do_status(self, arg: str) -> None:
        """Show current game status: STATUS"""
        if arg:
            self._print_error("STATUS command takes no arguments")
            return
        
        total_words = len(self.original_wordlist)
        current_words = len(self.current_wordlist)
        reduction_percent = ((total_words - current_words) / total_words * 100) if total_words > 0 else 0
        
        if RICH_AVAILABLE and self.console:
            table = Table(title="Game Status")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            table.add_row("Total words", str(total_words))
            table.add_row("Remaining words", str(current_words))
            table.add_row("Reduction", f"{reduction_percent:.1f}%")
            
            self.console.print(table)
        else:
            print(f"Total words: {total_words}")
            print(f"Remaining words: {current_words}")
            print(f"Reduction: {reduction_percent:.1f}%")
    
    def do_show(self, arg: str) -> None:
        """Show current possible words: SHOW [number]"""
        try:
            count = int(arg) if arg.strip() else 20
            if count <= 0:
                raise ValueError("Count must be positive")
        except ValueError:
            self._print_error("Please provide a valid positive number")
            return
        
        words = list(self.current_wordlist)[:count]
        if words:
            self._print_info(f"Showing {len(words)} possible words:")
            print(", ".join(sorted(words)))
        else:
            self._print_info("No possible words remaining!")
    
    def _get_top_choices(self, possible_words: Set[str], size: int = 10) -> List[str]:
        """Get top word choices prioritizing common words"""
        # First, get common words that are still possible
        common_choices = [word for word in self.common_words if word in possible_words]
        
        # If we need more words, add from remaining possible words
        if len(common_choices) < size:
            remaining_words = [word for word in possible_words if word not in common_choices]
            common_choices.extend(sorted(remaining_words)[:size - len(common_choices)])
        
        return common_choices[:size]
    
    def _display_recommendations(self, words: List[str]) -> None:
        """Display word recommendations in a formatted way"""
        if not words:
            self._print_info("No words remaining!")
            return
        
        count = len(self.current_wordlist)
        self._print_info(f"Top choices from {count} remaining words:")
        
        if RICH_AVAILABLE and self.console:
            # Display in a nice table
            table = Table()
            table.add_column("Rank", style="cyan")
            table.add_column("Word", style="green")
            table.add_column("Type", style="yellow")
            
            for i, word in enumerate(words, 1):
                word_type = "Common" if word in self.common_words else "Regular"
                table.add_row(str(i), word.upper(), word_type)
            
            self.console.print(table)
        else:
            for i, word in enumerate(words, 1):
                word_type = "(common)" if word in self.common_words else ""
                print(f"{i:2d}. {word.upper()} {word_type}")
    
    def do_bye(self, arg: str) -> bool:
        """Stop recording, close the window, and exit: BYE"""
        self._print_success('Thank you for using Wordle Solver!')
        self.close()
        return True
    
    def do_EOF(self, arg: str) -> bool:
        """Handle Ctrl+D to exit gracefully"""
        print()  # New line for clean exit
        return self.do_bye(arg)
    
    # Recording and playback functionality
    def do_record(self, arg: str) -> None:
        """Save future commands to filename: RECORD <filename>"""
        if not arg:
            self._print_error("Please specify a filename")
            return
        
        try:
            self.file = open(arg, 'w', encoding='utf-8')
            self._print_success(f"Recording commands to {arg}")
        except Exception as e:
            self._print_error(f"Cannot open file for recording: {e}")
    
    def do_playback(self, arg: str) -> None:
        """Playback commands from a file: PLAYBACK <filename>"""
        if not arg:
            self._print_error("Please specify a filename")
            return
        
        try:
            self.close()
            with self._safe_file_open(arg) as f:
                commands = [line.strip() for line in f if line.strip()]
                self.cmdqueue.extend(commands)
                self._print_success(f"Playing back {len(commands)} commands from {arg}")
        except Exception as e:
            self._print_error(f"Cannot playback from file: {e}")
    
    def precmd(self, line: str) -> str:
        """Process command before execution"""
        line = line.lower().strip()
        if self.file and 'playback' not in line:
            print(line, file=self.file)
        return line
    
    def close(self) -> None:
        """Clean up resources"""
        if self.file:
            try:
                self.file.close()
                self._print_info("Recording stopped")
            except Exception as e:
                self.logger.error(f"Error closing file: {e}")
            finally:
                self.file = None
    
    def emptyline(self) -> None:
        """Override to do nothing on empty line instead of repeating last command"""
        pass
    
    def default(self, line: str) -> None:
        """Handle unknown commands"""
        self._print_error(f"Unknown command: {line}. Type 'help' for available commands.")

import time
@dataclass
class GameState:
    """Represents the current state of a Wordle game"""
    guesses: List[str] = None
    remaining_words: Set[str] = None
    game_number: int = 1
    start_time: float = None
    is_solved: bool = False
    target_word: Optional[str] = None  # For practice mode
    
    def __post_init__(self):
        if self.guesses is None:
            self.guesses = []
        if self.remaining_words is None:
            self.remaining_words = set()
        if self.start_time is None:
            self.start_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'guesses': self.guesses,
            'remaining_words': list(self.remaining_words),
            'game_number': self.game_number,
            'start_time': self.start_time,
            'is_solved': self.is_solved,
            'target_word': self.target_word
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """Create from dictionary"""
        state = cls()
        state.guesses = data.get('guesses', [])
        state.remaining_words = set(data.get('remaining_words', []))
        state.game_number = data.get('game_number', 1)
        state.start_time = data.get('start_time', time.time())
        state.is_solved = data.get('is_solved', False)
        state.target_word = data.get('target_word')
        return state


def main():
    """Main entry point"""
    try:
        solver = WordleSolver()
        solver.cmdloop()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == '__main__':
    main()