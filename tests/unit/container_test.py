import pytest
import ouroboros.container as container
from container_object import container_object


@pytest.fixture()
def fake_container():
    return container_object


def test_new_container_properties(fake_container):
    latest = 'busybox:latest'
    new_container = container.new_container_properties(
        fake_container, new_image=latest)
    assert new_container['name'] == 'testName1'
    assert new_container['image'] == latest
    assert new_container['host_config'] == fake_container['HostConfig']
    assert new_container['labels'] == fake_container['Config']['Labels']
    assert new_container['entrypoint'] == fake_container['Config']['Entrypoint']
    assert new_container['environment'] == fake_container['Config']['Env']


def test_get_name(fake_container):
    assert container.get_name(fake_container) == 'testName1'


def test_to_monitor(mocker):
    mocker.patch.object(container.cli, 'api_client')
    container.cli.api_client.containers.return_value = []

    result = container.to_monitor(monitor='test')
    assert result == []
    container.cli.api_client.containers.assert_called_once()


def test_to_monitor_exception(mocker, caplog):
    mocker.patch.object(container.cli, 'api_client')
    container.cli.api_client.containers.side_effect = BaseException('I blew up!!')

    container.to_monitor(monitor='test')
    assert 'connect to Docker API' in caplog.text


def test_running_exception(mocker, caplog):
    mocker.patch.object(container.cli, 'api_client')
    container.cli.api_client.containers.side_effect = BaseException("I'm blasting off again!")

    container.running()
    assert 'connect to Docker API' in caplog.text