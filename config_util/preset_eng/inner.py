import copy
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

import toml
import yaml

SUPPORTED_PRESET_FORMATS = '.yml', ".json", ".toml"
log = logging.getLogger(__name__)


@dataclass
class PresetRegister:
    """Реестр файлов предустановок, осуществляет функции поиска, чтения, записи и раскрытия файлов (extends)"""

    __dirs: list[Path] = field(default_factory=list)  # директории, в которых будет осуществлен поиск файлов
    __loaded: dict[Path, dict] = field(default_factory=dict, init=False)  # уже загруженные файлы

    def __getitem__(self, item: str):
        extend_path = item.split(":")
        data = self.load(extend_path[0])
        for part in extend_path[1:]:
            data = data[part]
        return copy.deepcopy(data)

    @property
    def dirs(self):
        """Список доступных директорий с файлами предустановки"""
        return [Path(".")] + self.__dirs

    @property
    def presets(self) -> dict[str, Path]:
        """Доступные файлы предустановок"""
        def insert_preset(data, prs):
            name = PresetRegister.preset_name(prs)
            if name in data:
                log.warning(f"conflicting presets found: `{data[name]}` and `{prs}`. Replacing")
            data[name] = prs
            data[prs.stem] = prs

        presets = (Path(directory).joinpath(path)
                   for directory in self.dirs
                   for path in os.listdir(directory)
                   if PresetRegister.is_preset(Path(path)))

        out = {}
        for preset in presets:
            insert_preset(out, preset)
        return out

    def search_for(self, name: str) -> Path:
        def search_in_dir(directory: Path, n: str):
            for p in map(Path, os.listdir(directory)):
                if PresetRegister.is_preset(p):
                    if PresetRegister.preset_name(p) == n:
                        return directory.joinpath(p)
                    if PresetRegister.preset_name(directory.joinpath(p)) == n:
                        return directory.joinpath(p)

        path = Path(name)
        if path.exists():
            return path
        if path.parent.exists():
            log.debug(f"file `{path}` not found, searching in `{path.parent}`")
            found = search_in_dir(path.parent, name)
            if found is not None:
                return found
        name = PresetRegister.preset_name(Path(name))
        log.debug(f"searching `{name}` in local directory")
        found = search_in_dir(Path("."), name)
        if found is not None:
            return found
        presets = self.presets
        log.debug(f"searching `{name}` in presets register")
        if name in presets:
            return presets[name]
        log.critical(f"preset `{name}` not found.")
        raise FileNotFoundError(f"preset `{name}` not found.")

    @staticmethod
    def preset_name(path: Path):
        """Получает имя файла предустановок в том виде, как он будет доступен в реестре"""
        return "/".join(path.parts[:-1] + (path.stem,))

    @staticmethod
    def is_preset(path: Path):
        return path.suffix in SUPPORTED_PRESET_FORMATS

    @staticmethod
    def parse_preset(path: Path):
        with open(path) as file:
            match path.suffix:
                case ".yml":
                    parsed = yaml.load(file, yaml.FullLoader)
                    if parsed is None:
                        log.critical(f"`{path}` is empty")
                        raise EOFError(f"`{path}` is empty")
                    return parsed
                case ".json":
                    return json.load(file)
                case ".toml":
                    return toml.load(file)
            log.debug(f"parsed preset `{path}`")

    def load(self, name: str) -> dict:
        path = self.search_for(name)
        if path in self.__loaded:
            return self.__loaded[path]
        self.__loaded[path] = self.parse_preset(path)
        log.info(f"extending `{name}`")
        self.__loaded[path] = self.extend_dict(self.__loaded[path])
        log.debug(f"loaded new preset `{path}`")
        return self.__loaded[path]

    def dump(self, name, file: TextIO):
        suffix = Path(file.name).suffix
        if suffix not in SUPPORTED_PRESET_FORMATS:
            raise IOError(f'format `{suffix}` is not supported yet')
        match suffix:
            case ".yml":
                yaml.dump(self[name], file)
            case ".json":
                json.dump(self[name], file, indent=3)
            case ".toml":
                toml.dump(self[name], file)

    def write(self, name: str, path: Path):
        with open(path, "w") as file:
            self.dump(name, file)

    def extend(self, name: str):
        log.info(f"extending `{name}`")
        return self.extend_dict(self[name])

    def extend_dict(self, data: dict) -> dict:
        extended = {}
        if "extends" in data:
            parent = data.pop("extends")
            extended.update(self.extend_dict(self[parent]))
        for key, value in data.items():
            if isinstance(value, dict):
                value = self.extend_dict(value)
            extended[key] = value
        return extended
