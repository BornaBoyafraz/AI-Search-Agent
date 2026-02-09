# Path for filesystem writes, textwrap for formatting, typing for annotations.
from pathlib import Path
import textwrap
from typing import List

# Directory creation helper.
from .utils import ensure_dir


def write_output(path: Path, paragraph: str, sources: List[str], width: int = 100) -> None:
    # Ensure the output directory exists.
    ensure_dir(path.parent)
    # Wrap the paragraph to a fixed width for readability.
    wrapped = textwrap.fill(paragraph.strip(), width=width)
    # Compose the output file with a sources section.
    lines = [wrapped, "", "Sources:"]
    for url in sources:
        lines.append(url)
    # Write the final text to disk.
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
