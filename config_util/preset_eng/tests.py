import json
import os
from pathlib import Path

import pytest
import toml
import yaml

from preset_eng import PresetRegister

TEST_DATA = {
    "string": 'any str',
    "dict": {
        "int": 1,
        "bool": True,
        "float": .5,
        "list": [1, 2, 3]
    }
}


@pytest.fixture(scope="function")
def _change_test_dir(request):
    os.chdir("..")
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture()
def json_test_file_path():
    path = Path("test.json")
    with open(path, "w") as file:
        json.dump(TEST_DATA, file)
    yield path
    os.remove(path)


@pytest.fixture()
def yaml_test_file_path():
    path = Path("test.yml")
    with open(path, "w") as file:
        yaml.dump(TEST_DATA, file)
    yield path
    os.remove(path)


@pytest.fixture()
def toml_test_file_path():
    path = Path("test.toml")
    with open(path, "w") as file:
        toml.dump(TEST_DATA, file)
    yield path
    os.remove(path)


def test_parsing_yaml(yaml_test_file_path):
    assert TEST_DATA == PresetRegister.parse_preset(yaml_test_file_path)


def test_parsing_json(json_test_file_path):
    assert TEST_DATA == PresetRegister.parse_preset(json_test_file_path)


def test_parsing_toml(toml_test_file_path):
    assert TEST_DATA == PresetRegister.parse_preset(toml_test_file_path)


def test_from_readme(_change_test_dir):
    extended = PresetRegister().extend("examples/presets/another-demo")
    result = PresetRegister.parse_preset(Path("examples/presets/result.yml"))

    assert result == extended
