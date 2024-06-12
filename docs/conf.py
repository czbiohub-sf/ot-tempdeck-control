from pathlib import Path
import sys
sys.path.insert(0, str(Path("..").resolve()))


project = 'ot-tempdeck-control'
copyright = '2024, Greg Courville'
author = 'Greg Courville <greg.courville@czbiohub.org>'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.githubpages',
    ]

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'classic'
