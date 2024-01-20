#!/usr/bin/env python3

from aws_cdk import App

from stacks.BackendStack import BackendStack

app = App()
BackendStack(app, "MartianDiceBackend", env = { 'region': 'eu-west-1' })

app.synth()