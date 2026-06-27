"""
setup.py -- KDP Research Pipeline

Install dependencies:
    pip install -r requirements.txt

PyInstaller packaging (produces dist/KDP_Pipeline.exe):
    pip install pyinstaller
    pyinstaller build.spec

For development (editable install):
    pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="kdp-research-pipeline",
    version="1.0.0",
    description="Amazon KDP Niche Research Pipeline — scrape / score / export",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "kdp-pipeline=main:cli",
        ],
    },
)
