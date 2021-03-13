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
        "aws-cdk.core==1.92.0",
		"aws-cdk.aws_apigatewayv2==1.92.0",
		"aws-cdk.aws_apigatewayv2_integrations==1.92.0",
        "aws-cdk.aws_lambda==1.92.0",
		"aws-cdk.aws_elasticache==1.92.0"
    ],

    python_requires=">=3.6",
)
