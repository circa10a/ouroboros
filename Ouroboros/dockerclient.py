from logging import getLogger
from docker import DockerClient
from docker.errors import DockerException, APIError

from Ouroboros.helpers import set_properties


class Docker(object):
    def __init__(self, config):
        self.config = config
        self.client = DockerClient(base_url=self.config.docker_socket)

        self.logger = getLogger()
        self.monitored = self.monitor_filter()

    def get_running(self):
        """Return running container objects list, except ouroboros itself"""
        running_containers = []
        try:
            for container in self.client.containers.list(filters={'status': 'running'}):
                if 'ouroboros' not in container.image.tags[0]:
                    running_containers.append(container)

        except DockerException:
            self.logger.critical("Can't connect to Docker API at %s", self.config.docker_socket)
            exit(1)

        return running_containers

    def monitor_filter(self):
        """Return filtered running container objects list"""
        running_containers = self.get_running()

        if self.config.monitor:
            running_containers = [container for container in running_containers
                                  if container.name in self.config.monitor]

        if self.config.ignore:
            self.logger.info("Ignoring container(s): %s", ", ".join(self.config.ignore))
            running_containers = [container for container in running_containers
                                  if container.name not in self.config.ignore]

        return running_containers

    def pull(self, image_object):
        """Docker pull image tag/latest"""
        image = image_object
        tag = image.tags[0]
        if self.config.latest and image.tags[0][-6:] != 'latest':
            tag = tag.split(':')[0] + ':latest'

        self.logger.debug('Pulling tag: %s', tag)
        if self.config.auth_json:
            return_image = self.client.images.pull(tag, auth_config=self.config.auth_json)
        else:
            return_image = self.client.images.pull(tag)

        return return_image

    def update_containers(self):
        updated_count = 0
        metrics.monitored_containers(num=len(self.monitored))

        for container in self.monitored:
            current_image = container.image

            try:
                latest_image = self.pull(current_image)
            except APIError as e:
                self.logger.error(e)
                continue

            # If current running container is running latest image
            if current_image.id != latest_image.id:
                self.logger.info('%s will be updated', container.name)

                # new container dict to create new container from
                new_config = set_properties(old=container, new=latest_image)

                self.logger.debug('Stopping container: %s', container.name)
                container.stop(container)

                self.logger.debug('Removing container: %s', container.name)
                container.remove(container)

                created = self.client.api.create_container(**new_config)
                new_container = self.client.containers.get(created.get("Id"))
                new_container.start()

                if self.config.cleanup:
                    current_image.remove()

                updated_count += 1

                metrics.container_updates(label='all')
                metrics.container_updates(label=container.name)

                if self.config.webhook_urls:
                    webhook.post(urls=args.webhook_urls, container_name=container_name, old_sha=current_image['Id'], new_sha=latest_image['Id'])
