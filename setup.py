"""Setup script for Vibe Verifier."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="vibe-verifier",
    version="0.1.0",
    author="Vibe Verifier Team",
    description="A comprehensive tool for code complexity analysis, formal verification, and testing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vibes/vibe-verifier",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vibe-verifier=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["*.json", "*.yaml", "*.yml"],
    },
)