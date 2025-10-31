from setuptools import setup

setup(
    name="restriction-module",
    py_modules=["restriction_module"],
    description="A Synapse module for restricting user actions like leaving rooms or deactivating accounts.",
    install_requires=[
        "matrix-synapse>=1.37.0",  # Adjust based on your Synapse version; ensures compatibility
    ],
    version="0.1.0",
    python_requires=">=3.7",
)
