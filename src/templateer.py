"""
Simple pure-Python, dependency-free template processor.

Template variables are surrounded by `@@`. Template variables can be passed
in the environment:

    VAR1=foo templateer -t example-with-var1.txt -o output.txt

Or in an env/ini-without-sections file:

    templateer -i vars.ini -t example.tpl -o output.txt

Or edited interactively:

    templateer --edit -t example.tpl -o output.txt

Or all three combined:

    VAR1=foo templateer --edit -i vars.ini -t example.tpl -o output.txt

If `--edit` is not provided, the user will be prompted for values of variables
not provided in the environment or an input file.

Variables in a template can be listed with `--list`.

Variables are sorted for prompt and edit modes and can begin with a digit.

NB: use the `env` command to provide variables starting with a digit as
environment variables; otherwise some shells do not recognize the prefixed
variable assignment. I.e., this works:

    env 1_VAR=xxx templateer ...

But this does not:

    1_VAR=xxx templateer ...
    -bash: 1_VAR=xxx: command not found

"""

import argparse
import configparser
import itertools
import os
import re
import subprocess
import tempfile
from typing import ChainMap, List, Mapping


def parse_template(template: str) -> List[str]:
    """Extracts variable names from a template string.

    :param template: The template content, with variables denoted by @@var@@.
    :type template: str
    :return: A list of unique variable names found in the template.
    :rtype: List[str]
    """
    variables = []
    for result in re.findall(r'@@(\w+)@@', template):
        if result not in variables:
            variables.append(result)

    return variables


def prompt_variables(variables: List[str]) -> Mapping[str, str]:
    """Prompts the user to enter values for a list of variables.

    :param variables: A list of variable names to prompt for.
    :type variables: List[str]
    :return: A mapping of variable names to their user-provided values.
    :rtype: Mapping[str, str]
    """
    variables_map = {}
    for variable in variables:
        variables_map[variable] = input(f'{variable} = ')

    return variables_map


def env_variables(variables: List[str], env=os.environ) -> Mapping[str, str]:
    """Retrieves variable values from environment variables.

    :param variables: A list of variable names to look for in the environment.
    :type variables: List[str]
    :param env: The environment to search in, defaults to os.environ.
    :type env: Mapping, optional
    :return: A mapping of variable names to their values if found in the environment.
    :rtype: Mapping[str, str]
    """
    variables_map = {}
    for variable in variables:
        if variable in env:
            variables_map[variable] = env[variable]

    return variables_map


def ini_variables(variables: List[str], file) -> Mapping[str, str]:
    """Reads variable values from an INI-style file.

    The file is expected to have no [templateer] section and can have no
    section at all.

    :param variables: A list of variable names to look for in the file.
    :type variables: List[str]
    :param file: A file-like object to read from.
    :type file: file
    :return: A mapping of variable names to their values if found in the file.
    :rtype: Mapping[str, str]
    """
    if not file:
        return {}

    # Reset file pointer in case it has been read before
    file.seek(0)
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


def fill_variables(
    variables: List[str], input_file=None, interactive=True
) -> Mapping[str, str]:
    """Orchestrates filling variables from different sources.

    The precedence for variable values is:
    1. User prompt (if interactive)
    2. Environment variables
    3. INI file

    :param variables: A list of variable names to fill.
    :type variables: List[str]
    :param input_file: A file-like object for an INI file, defaults to None
    :type input_file: file, optional
    :param interactive: If True, prompt the user for missing variables, defaults to True
    :type interactive: bool, optional
    :return: A ChainMap containing the filled variables.
    :rtype: Mapping[str, str]
    """
    env_map = env_variables(variables)
    ini_map = ini_variables(variables, input_file)

    # Precedence for pre-population and non-interactive is env > ini
    pre_population_map = ChainMap(env_map, ini_map)

    if interactive:
        # For interactive mode, we prompt for anything not in env or ini.
        # Precedence: prompt > env > ini
        vars_to_prompt = [v for v in variables if v not in pre_population_map]
        prompt_map = prompt_variables(vars_to_prompt)
        return ChainMap(prompt_map, pre_population_map)
    else:
        # For non-interactive (e.g., --edit pre-population), just return the layered map.
        return pre_population_map


def expand_template(template: str, variables: Mapping[str, str]) -> str:
    """Replaces placeholders in the template with their corresponding values.

    :param template: The template string.
    :type template: str
    :param variables: A mapping of variable names to their values.
    :type variables: Mapping[str, str]
    :return: The expanded template string.
    :rtype: str
    """
    for key, value in variables.items():
        template = template.replace(f'@@{key}@@', value)
    return template


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments.

    :return: An argparse.Namespace object containing the parsed arguments.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--template',
        '-t',
        nargs='?',
        type=argparse.FileType('r'),
        required=True,
    )
    parser.add_argument(
        '--input',
        '-i',
        nargs='?',
        type=argparse.FileType('r'),
        help='Variable input file. Formatted as env/ini-without-section.',
    )
    parser.add_argument(
        '--edit',
        '-e',
        action='store_true',
        help='Edit variables interactively in an editor.',
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', '-o', nargs='?', type=argparse.FileType('w'))
    group.add_argument(
        '--list-variables',
        '--list',
        '-l',
        action='store_true',
        help='List available template variables',
    )

    return parser.parse_args()


def output_variables(template: str):
    """Prints the variables found in a template.

    :param template: The template string.
    :type template: str
    """
    variables = parse_template(template)
    print('Variables:')
    for variable in variables:
        print(variable)


def main():
    """The main entry point of the script."""
    args = parse_args()

    template: str = args.template.read()

    if args.list_variables:
        output_variables(template)
        return

    template_vars = parse_template(template)
    variables = None

    if args.edit:
        # Pre-populate with --input and environment variables
        pre_populated_vars = fill_variables(
            template_vars, args.input, interactive=False
        )

        with tempfile.NamedTemporaryFile(
            mode='w+', delete=False, suffix='.ini'
        ) as tmpfile:
            for var in template_vars:
                value = pre_populated_vars.get(var, '')
                tmpfile.write(f'{var}={value}\n')
            tmpfile.flush()
            tmpfile_path = tmpfile.name

        editor = os.environ.get('VISUAL') or os.environ.get('EDITOR') or 'vi'
        try:
            subprocess.run([editor, tmpfile_path], check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"Editor '{editor}' failed: {e}")
            os.remove(tmpfile_path)
            return

        with open(tmpfile_path, 'r') as f:
            # The edited file is the source of truth, do not re-apply other sources.
            variables = ini_variables(template_vars, f)
        os.remove(tmpfile_path)
    else:
        variables = fill_variables(template_vars, args.input)

    if variables:
        args.output.write(expand_template(template, variables))


if __name__ == '__main__':
    main()
