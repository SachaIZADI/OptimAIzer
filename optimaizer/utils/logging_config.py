import logging
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Custom logging formatter with colors for different log levels."""

    COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, Fore.WHITE)
        log_fmt = f"[{Fore.CYAN}%(asctime)s{Style.RESET_ALL}][{log_color}%(levelname)s{Style.RESET_ALL}]: %(message)s"
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


# Create handlers
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())


# Set up the logger
logger = logging.getLogger("optimaizer")
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
