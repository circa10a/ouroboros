import logging
import cli

log = logging.getLogger(__name__)


def new_container_properties(old_container, new_image):
    """Store object for spawning new container in place of the one with outdated image"""
    props = {
        'name': get_name(old_container),
        'image': new_image,
        'command': old_container['Config']['Cmd'],
        'host_config': old_container['HostConfig'],
        'labels': old_container['Config']['Labels'],
        'entrypoint': old_container['Config']['Entrypoint'],
        'environment': old_container['Config']['Env']
    }
    return props


def running():
    """Return running container objects list"""
    running_containers = []
    try:
        for container in cli.api_client.containers(
                filters={'status': 'running'}):
            if 'ouroboros' not in container['Image']:
                running_containers.append(
                    cli.api_client.inspect_container(container))
        return running_containers
    except BaseException:
        log.critical(
            f'Can\'t connect to Docker API at {cli.api_client.base_url}')


def to_monitor(monitor=None):
    """Return filtered running container objects list"""
    running_containers = []
    try:
        if monitor:
            for container in cli.api_client.containers(
                    filters={'name': monitor, 'status': 'running'}):
                running_containers.append(
                    cli.api_client.inspect_container(container))
        else:
            running_containers.extend(running())
        log.info(f'{len(running_containers)} running container(s) matched filter')
        return running_containers
    except BaseException:
        log.critical(
            f'Can\'t connect to Docker API at {cli.api_client.base_url}')


def get_name(container_object):
    """Parse out first name of container"""
    return container_object['Name'].replace('/', '')


def stop(container_object):
    """Stop out of date container"""
    log.debug(f'Stopping container: {get_name(container_object)}')
    return cli.api_client.stop(container_object)


def remove(container_object):
    """Remove out of date container"""
    log.debug(f'Removing container: {get_name(container_object)}')
    return cli.api_client.remove_container(container_object)


def create_new(config):
    """Create new container with latest image"""
    return cli.api_client.create_container(**config)


def start(container_object):
    """Start newly created container with latest image"""
    log.debug(f"Starting container: {container_object['Id']}")
    return cli.api_client.start(container_object)
