#!/usr/bin/env python

import click
import deployment
import json

@click.command()
@click.option('--config', default='./.djconfig', help='Path to configuration file.')
def deploy(config):
    try:
        with open(config) as data_file:
            data = json.load(data_file)
            print data
            deployment.deploy_stack(data)
    except IOError as err:
        print 'Failed to open configuration file at ' + config
        print err


if __name__ == '__main__':
    deploy()