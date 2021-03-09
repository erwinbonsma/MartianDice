#!/usr/bin/env python3

from aws_cdk import core

from stacks.BackendStack import BackendStack


app = core.App()
BackendStack(app, "MartianDiceBackend", env={'region': 'eu-west-1'})

app.synth()