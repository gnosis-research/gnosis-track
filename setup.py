#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gnosis-track",
    version="1.0.0",
    author="Gnosis Research",
    author_email="support@gnosis-research.com",
    description="Open Source Centralized Logging for Bittensor Subnets and AI Validators",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gnosis-research/gnosis-track",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: System :: Logging",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "ui": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "jinja2>=3.1.0",
        ],
        "monitoring": [
            "prometheus-client>=0.18.0",
            "grafana-api>=1.0.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "gnosis-track=gnosis_track.cli.main:main",
            "gnosis-track-ui=gnosis_track.ui.server:main",
            "gnosis-track-install=gnosis_track.deployment.installer:main",
        ],
    },
    include_package_data=True,
    package_data={
        "gnosis_track": [
            "ui/static/*",
            "ui/templates/*",
            "config/*.yaml",
            "deployment/docker/*",
        ],
    },
    zip_safe=False,
)