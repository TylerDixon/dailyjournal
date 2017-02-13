#!/usr/bin/env python

import click
import deployment
import json

@click.command()
@click.option('--config', default='./.djconfig', help='Path to configuration file.')
@click.option('--debug_npm', default=False, help='Show the npm output')
def deploy(config, debug_npm):
    try:
        with open(config) as data_file:
            data = json.load(data_file)
            deployment.deploy_stack(data, debug_npm)
    except IOError as err:
        print 'Failed to open configuration file at ' + config
        print err


if __name__ == '__main__':
    deploy()