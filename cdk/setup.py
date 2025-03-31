import setuptools

with open("README.md") as fp:
    long_description = fp.read()

setuptools.setup(
    name="martian-dice",
    version="0.0.1",

    description="Martian Dice cloud deployment",

    author="erwinbonsma",

    package_dir={"": "stacks"},
    packages=setuptools.find_packages(where="stacks"),

    install_requires=[
        "aws-cdk-lib>=2.0.0",
        "constructs>=10.0.0",
    ],

    python_requires=">=3.11",
)
