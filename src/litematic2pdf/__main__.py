"""Enable `python -m litematic2pdf <file.litematic>`."""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
