import argparse
import json
import sys
from pathlib import Path
import os

import toml
import yaml

from preset_eng import PresetRegister


autotest_path = Path(os.getenv("autotest_program"))
case_path = Path(os.getenv("case_path"))

path_list = [autotest_path, case_path, autotest_path / "Lazurit" / "presets"]
for i in os.listdir(case_path):
    path_list.append(case_path / i)
register = PresetRegister(
    path_list
)
__version__ = (0, 1, 0)

args = 'preset show'.split()


class ShowVersion(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print("autotest", ".".join(map(str, __version__)))
        parser.exit(0)


class PresetShow(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        data_path = register.search_for(values)
        if namespace.extend:
            data = register.extend(values)
        else:
            data = register.parse_preset(data_path)
        format_ = namespace.format or data_path.suffix or Path(values).suffix or '.yml'
        match format_:
            case '.yml':
                string = yaml.dump(data)
            case '.json':
                string = json.dumps(data, indent=3)
            case '.toml':
                string = toml.dumps(data)
            case _ as form:
                raise TypeError(f"unknown format `{form}`")
        if namespace.output is None:
            print(string)
        else:
            with open(namespace.output, "w") as file:
                format_ = Path(namespace.output).suffix if namespace.format is None else format_
                match format_:
                    case '.yml':
                        yaml.dump(data, file)
                    case '.json':
                        json.dump(data, file, indent=3)
                    case '.toml':
                        toml.dump(data, file)
                    case _ as format_:
                        raise TypeError(f"unknown format `{format_}`")
        parser.exit(0)


class ShowPath(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(register.search_for(values))
        parser.exit(0)


class ShowAbsPath(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(register.search_for(values).absolute())
        parser.exit(0)


class PresetList(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        presets = register.presets
        if presets:
            max_name = max(map(lambda e: len(e), presets.keys()))
            max_path = max(map(lambda e: len(str(e.absolute()) if namespace.abs_path else str(e)), presets.values()))
            print(f"{'name'.center(max_name)} | {'path'.center(max_path)}\n"
                  f"{''.rjust(max_name + 1, '-')}|{''.rjust(max_path + 1, '-')}")
            for key, value in presets.items():
                print(f"{key.ljust(max_name)} | {value.absolute() if namespace.abs_path else value}")
        else:
            print("no available presets")
        parser.exit(0)


if __name__ == '__main__':
    print(sys.argv[1:])
    global_parser = argparse.ArgumentParser(prog='autotest')
    subparsers = global_parser.add_subparsers()

    preset = subparsers.add_parser("preset", help="actions with preset files - reading, writing, inspecting")
    config = subparsers.add_parser("config", help="configuration of autotest application")
    config.add_argument("-f",
                        )
    global_parser.add_argument('-v', '--version',
                               action=ShowVersion, nargs=1,
                               help='show current version of autotest application')

    preset_subparsers = preset.add_subparsers()
    preset_show = preset_subparsers.add_parser('show', help='read preset')
    preset_list = preset_subparsers.add_parser("list", help="list of all visible presets")
    preset_list.add_argument("empty", nargs=0, action=PresetList)
    preset_list.add_argument('-a', '--abs-path', action='store_true', help="show absolute paths")

    preset_show.add_argument('name', action=PresetShow, help='name of preset')
    preset_show.add_argument("-p", "--path", action=ShowPath, help='show path to preset', metavar="NAME")
    preset_show.add_argument("-a", "--abs-path", action=ShowAbsPath, help='show absolute path to preset',
                             metavar="NAME")
    preset_show.add_argument("-e", "--extend",
                             action="store_true", help="extend file")
    preset_show.add_argument("-o", '--output', help="output file if not - print to std")
    preset_show.add_argument("-f", "--format",
                             choices=['.yml', '.json', '.toml'],
                             help='specify output format. If not, uses file extension or .yml')

    parsed = global_parser.parse_args(sys.argv[1:])
