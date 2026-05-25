from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agent-eye",
    version="0.1.0",
    description="An intelligent visual discrepancy and layout feedback engine for AI Coding Agents.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="lihanlei",
    url="https://github.com/steveleeh/agent-eye",
    packages=find_packages(),
    install_requires=[
        "opencv-python-headless>=4.8.0",
        "scikit-image>=0.21.0",
        "numpy>=1.24.0",
        "pillow>=9.5.0",
    ],
    entry_points={
        "console_scripts": [
            "agent-eye=agent_eye.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
