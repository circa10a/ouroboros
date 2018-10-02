import docker
import logging
import defaults
from main import api_client

class NewContainerProperties:
    def __init__(self, old_container, new_image):
        """
        Store object for spawning new container in place of the one with outdated image
        """
        self.name = old_container['Names'][0].replace('/','')
        self.image = new_image
        self.command = old_container['Command']
        self.ports = self.get_container_ports(old_container['Ports'])
        self.host_config = api_client.create_host_config(port_bindings=self.create_host_port_bindings(old_container['Ports']),
                                                        binds=self.create_host_volume_bindings(old_container['Mounts']),
                                                        restart_policy=defaults.RESTART_POLICY)
        self.labels = old_container['Labels']
        self.networking_config = api_client.create_networking_config({ self.get_network_name(old_container['NetworkSettings']['Networks']): api_client.create_networking_config() })
        self.volumes = self.get_volumes(old_container['Mounts'])
        self.detach = True
        if 'Entrypoint' in old_container:
            self.entrypoint = old_container['Entrypoint']

    def get_network_name(self, net_config):
        """Get first container network name (Only supports 1 network)"""
        return next(iter(net_config))

    def get_container_ports(self, port_list):
        """Get exposed container ports"""
        container_port_list = []
        for i in port_list:
            container_port_list.append(i['PrivatePort'])
        return container_port_list

    def create_host_port_bindings(self, port_list):
        """Create host_config port bindings dictionary"""
        port_bindings = {}
        for port in port_list:
            port_bindings.update({ port['PrivatePort']:port['PublicPort'] })
        return port_bindings

    def get_volumes(self, volume_list):
        """Get mapped container volumes"""
        container_volume_list = []
        for volume in volume_list:
            container_volume_list.append('{}:{}'.format(volume['Source'], volume['Destination']))
        return container_volume_list

    def create_host_volume_bindings(self, volume_list):
        """Create host_config volume bindings dictionary"""
        volume_bindings = {}
        volume_source = ''
        for volume in volume_list:
            if 'Name' in volume:
                volume_source = volume['Name']
            else:
                volume_source = volume['Source']
            volume_bindings.update({
                volume_source: {
                    'bind': volume['Destination'],
                    'mode': volume['Mode']
                }
            })
        return volume_bindings

def running():
    try:
        return  api_client.containers()
    except:
        logging.critical(('Can\'t connect to Docker API at {}').format(api_client.base_url))

def to_monitor():
    """Return container object list"""
    container_list = []
    for container in running():
        container_list.append(get_name(container))
    logging.debug(('Monitoring containers: {}').format(container_list))
    return running()

def get_name(container_object):
    """Parse out first name of container"""
    return container_object['Names'][0].replace('/','')

def stop(container_object):
    """Stop out of date container"""
    logging.debug(('Stopping container: {}').format(get_name(container_object)))
    return api_client.stop(container_object)

def remove(container_object):
    """Remove out of date container"""
    logging.debug(('Removing container: {}').format(get_name(container_object)))
    return api_client.remove_container(container_object)

def create_new_container(config):
    """Create new container with latest image"""
    logging.debug(('Creating new container with opts: {}').format(config))
    return api_client.create_container(**config)

def start(container_object):
    """Start newly created container with latest image"""
    logging.debug(('Starting container: {}').format(container_object))
    return api_client.start(container_object)
