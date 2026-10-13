"""English is the default tutorial language."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name('build_tutorial_en.py')), run_name='__main__')
