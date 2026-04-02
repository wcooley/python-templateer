# Copyright (c) 2026 Wil Cooley
# SPDX-License-Identifier: MIT

"""Tests for the templateer script."""
import io
from unittest.mock import patch
import templateer


def test_parse_template():
    """Verify that variables are correctly parsed from a template string."""
    template = 'Hello, @@name@@! Welcome to @@place@@.'
    variables = templateer.parse_template(template)
    assert variables == ['name', 'place']


def test_env_variables():
    """Verify that variables are correctly read from environment variables."""
    variables = ['name', 'place']
    env = {'name': 'World'}
    env_vars = templateer.env_variables(variables, env)
    assert env_vars == {'name': 'World'}


def test_ini_variables():
    """Verify that variables are correctly read from an INI file."""
    variables = ['name', 'place']
    ini_content = 'name = World\n'
    ini_file = io.StringIO(ini_content)
    ini_vars = templateer.ini_variables(variables, ini_file)
    assert ini_vars == {'name': 'World'}


def test_fill_variables_with_ini():
    """Verify that variables are filled from INI and user prompt correctly."""
    variables = ['name', 'place']
    ini_content = 'name = World\n'
    ini_file = io.StringIO(ini_content)

    # Mock prompt_variables to avoid waiting for user input
    with patch(
        'templateer.prompt_variables', return_value={'place': 'Universe'}
    ):
        all_vars = templateer.fill_variables(variables, ini_file)
        assert all_vars['name'] == 'World'
        assert all_vars['place'] == 'Universe'


def test_expand_template():
    """Verify that a template is correctly expanded with given variables."""
    template = 'Hello, @@name@@! Welcome to @@place@@.'
    variables = {'name': 'World', 'place': 'Universe'}
    expanded = templateer.expand_template(template, variables)
    assert expanded == 'Hello, World! Welcome to Universe.'


def test_integration_with_input_file(monkeypatch, tmp_path):
    """Test the full flow with template, input, and output files."""
    template_content = 'Hello, @@name@@!'
    template_file = tmp_path / 'template.txt'
    template_file.write_text(template_content)

    ini_content = 'name = from file\n'
    ini_file = tmp_path / 'vars.ini'
    ini_file.write_text(ini_content)

    output_file = tmp_path / 'output.txt'

    # Mock sys.argv
    monkeypatch.setattr(
        'sys.argv',
        [
            'templateer',
            '-t',
            str(template_file),
            '-i',
            str(ini_file),
            '-o',
            str(output_file),
        ],
    )

    templateer.main()

    assert output_file.read_text() == 'Hello, from file!'


@patch('subprocess.run')
def test_edit_flow(mock_subprocess_run, monkeypatch, tmp_path):
    """Test the --edit flow, simulating user input via an editor."""
    template_content = 'Hello, @@name@@, welcome to @@place@@!'
    template_file = tmp_path / 'template.txt'
    template_file.write_text(template_content)

    output_file = tmp_path / 'output.txt'

    # Simulate the user editing the file
    def side_effect(command, check):
        editor_file_path = command[1]
        with open(editor_file_path, 'w') as f:
            f.write('name=edited_name\n')
            f.write('place=edited_place\n')

    mock_subprocess_run.side_effect = side_effect

    monkeypatch.setattr(
        'sys.argv',
        [
            'templateer',
            '-t',
            str(template_file),
            '-e',
            '-o',
            str(output_file),
        ],
    )

    # Set EDITOR environment variable for the test
    monkeypatch.setenv('EDITOR', 'my_editor')
    monkeypatch.setenv('VISUAL', 'my_editor')

    templateer.main()

    assert (
        output_file.read_text()
        == 'Hello, edited_name, welcome to edited_place!'
    )
    mock_subprocess_run.assert_called_once()
    assert mock_subprocess_run.call_args[0][0][0] == 'my_editor'


@patch('subprocess.run')
def test_edit_with_input_and_env(mock_subprocess_run, monkeypatch, tmp_path):
    """Test --edit with pre-population from --input and environment variables."""
    template_content = (
        'Hello, @@name@@, welcome to @@place@@. Your role is @@role@@.'
    )
    template_file = tmp_path / 'template.txt'
    template_file.write_text(template_content)

    ini_content = 'name = from_ini\nplace = from_ini\n'
    ini_file = tmp_path / 'vars.ini'
    ini_file.write_text(ini_content)

    output_file = tmp_path / 'output.txt'

    # Simulate the user editing the file
    def side_effect(command, check):
        editor_file_path = command[1]
        # Check pre-population
        with open(editor_file_path, 'r') as f:
            content = f.read()
            assert 'name=from_env' in content  # env overrides ini
            assert 'place=from_ini' in content  # from ini
            assert 'role=' in content  # empty value, not in env or ini
        # Simulate edits
        with open(editor_file_path, 'w') as f:
            f.write('name=edited_name\n')
            f.write('place=edited_place\n')
            f.write('role=edited_role\n')

    mock_subprocess_run.side_effect = side_effect

    monkeypatch.setattr(
        'sys.argv',
        [
            'templateer',
            '-t',
            str(template_file),
            '-i',
            str(ini_file),
            '-e',
            '-o',
            str(output_file),
        ],
    )

    monkeypatch.setenv('VISUAL', 'my_editor')
    monkeypatch.setenv('EDITOR', 'my_editor')
    monkeypatch.setenv('name', 'from_env')

    templateer.main()

    assert (
        output_file.read_text()
        == 'Hello, edited_name, welcome to edited_place. Your role is edited_role.'
    )
    mock_subprocess_run.assert_called_once()
