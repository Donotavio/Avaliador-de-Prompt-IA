from setuptools import setup, find_packages

setup(
    name="prompt_evaluator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["fastapi", "uvicorn", "pydantic"],
)
