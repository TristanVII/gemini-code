from setuptools import setup, find_packages

setup(
    name="geminicode-cli",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "geminicode = geminicode.main:run",
        ],
    },
    author="Your Name",  # Consider changing this
    author_email="your.email@example.com",  # Consider changing this
    description="A simple CLI tool to print the launch directory.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/geminicode-cli",  # Optional: Add your repo URL
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Choose an appropriate license
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)

