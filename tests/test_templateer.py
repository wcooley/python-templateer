
import io
import templateer

def test_parse_template():
    template = "Hello, @@name@@! Welcome to @@place@@."
    variables = templateer.parse_template(template)
    assert variables == ["name", "place"]

def test_env_variables():
    variables = ["name", "place"]
    env = {"name": "World"}
    env_vars = templateer.env_variables(variables, env)
    assert env_vars == {"name": "World"}

def test_ini_variables():
    variables = ["name", "place"]
    ini_content = "name = World\n"
    ini_file = io.StringIO(ini_content)
    ini_vars = templateer.ini_variables(variables, ini_file)
    assert ini_vars == {"name": "World"}

def test_fill_variables_with_ini():
    variables = ["name", "place"]
    ini_content = "name = World\n"
    ini_file = io.StringIO(ini_content)
    
    # Mock prompt_variables to avoid waiting for user input
    templateer.prompt_variables = lambda vars: {"place": "Universe"}
    
    all_vars = templateer.fill_variables(variables, ini_file)
    assert all_vars["name"] == "World"
    assert all_vars["place"] == "Universe"

def test_expand_template():
    template = "Hello, @@name@@! Welcome to @@place@@."
    variables = {"name": "World", "place": "Universe"}
    expanded = templateer.expand_template(template, variables)
    assert expanded == "Hello, World! Welcome to Universe."

def test_integration_with_input_file(monkeypatch, tmp_path):
    template_content = "Hello, @@name@@!"
    template_file = tmp_path / "template.txt"
    template_file.write_text(template_content)

    ini_content = "name = from file\n"
    ini_file = tmp_path / "vars.ini"
    ini_file.write_text(ini_content)

    output_file = tmp_path / "output.txt"

    # Mock sys.argv
    monkeypatch.setattr(
        "sys.argv",
        [
            "templateer",
            "-t",
            str(template_file),
            "-i",
            str(ini_file),
            "-o",
            str(output_file),
        ],
    )

    templateer.main()

    assert output_file.read_text() == "Hello, from file!"
