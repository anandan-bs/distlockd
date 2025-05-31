from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="distlockd",
    version="1.0.3",
    author="Anandan B S",
    author_email="anandanklnce@gmail.com",
    description="Simple distributed lock daemon over TCP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anandan-bs/distlockd",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[],
    entry_points={
        'console_scripts': [
            'distlockd=distlockd.cli:main',
        ],
    },
    package_data={
        'distlockd': ['benchmarks/*'],
    },
    include_package_data=True,
)
