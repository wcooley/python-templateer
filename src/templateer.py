"""
Simple pure-Python, dependency-free template processor.

Template variables are surrounded by `@@`. Template variables can be passed
in the environment:

    VAR1=foo templateer -t example-with-var1.txt -o output.txt

If not provided in the environment, templateer will prompt the user for values.
"""

import argparse
import configparser
import itertools
import os
import re
from typing import ChainMap, List, Mapping


def parse_template(template: str) -> List[str]:
    variables = []
    for result in re.findall(r'@@(\w+)@@', template):
        if result not in variables:
            variables.append(result)

    return variables


def prompt_variables(variables: List[str]) -> Mapping[str, str]:
    variables_map = {}
    for variable in variables:
        variables_map[variable] = input(f'{variable} = ')

    return variables_map


def env_variables(variables: List[str], env=os.environ) -> Mapping[str, str]:
    variables_map = {}
    for variable in variables:
        if variable in env:
            variables_map[variable] = env[variable]

    return variables_map


def ini_variables(variables: List[str], file) -> Mapping[str, str]:
    if not file:
        return {}

    config = configparser.ConfigParser()
    # Prepend a [templateer] section so the input does not need one
    config.read_file(itertools.chain(['[templateer]'], file))

    variables_map = {}
    # Variables are in the [templateer] section
    if 'templateer' in config:
        for variable in variables:
            if variable in config['templateer']:
                variables_map[variable] = config['templateer'][variable]

    return variables_map


def fill_variables(variables: List[str], input_file=None) -> Mapping[str, str]:
    vars_to_process = list(variables)

    env_map = env_variables(vars_to_process)
    for var in env_map:
        vars_to_process.remove(var)

    ini_map = {}
    if input_file:
        ini_map = ini_variables(vars_to_process, input_file)
        for var in ini_map:
            vars_to_process.remove(var)

    prompt_map = prompt_variables(vars_to_process)

    return ChainMap(prompt_map, ini_map, env_map)


def expand_template(template: str, variables: Mapping[str, str]) -> str:
    for key, value in variables.items():
        template = template.replace(f'@@{key}@@', value)
    return template


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--template', '-t', nargs='?',
                        type=argparse.FileType('r'), required=True)
    parser.add_argument('--input', '-i', nargs='?',
                        type=argparse.FileType('r'),
                        help='Variable input file. Formatted as env/ini-without-section.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', '-o', nargs='?',
                        type=argparse.FileType('w'))
    group.add_argument('--list-variables', '--list', '-l',
                       action='store_true',
                        help='List available template variables')

    return parser.parse_args()


def output_variables(template: str):
    variables = parse_template(template)
    print('Variables:')
    for variable in variables:
        print(variable)


def main():
    args = parse_args()

    template: str = args.template.read()

    if args.list_variables:
        output_variables(template)
    else:
        variables = fill_variables(parse_template(template), args.input)
        args.output.write(expand_template(template, variables))


if __name__ == '__main__':
    main()
