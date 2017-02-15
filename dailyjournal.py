#!/usr/bin/env python

import click
import deployment

@click.command()
@click.option('--config', default='./.djconfig', help='Path to configuration file.')
@click.option('--debug_npm', default=False, help='Show the npm output')
def deploy(config, debug_npm):
    loaded_config = deployment.get_config(config)
    if loaded_config == None:
        return
    deployment.deploy_stack(loaded_config, debug_npm)


if __name__ == '__main__':
    deploy()