
# Templateer

```
usage: templateer [-h] --template [TEMPLATE] [--input [INPUT]] [--edit]
                  (--output [OUTPUT] | --list-variables)

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

optional arguments:
  -h, --help            show this help message and exit
  --template [TEMPLATE], -t [TEMPLATE]
  --input [INPUT], -i [INPUT]
                        Variable input file. Formatted as env/ini-without-
                        section.
  --edit, -e            Edit variables interactively in an editor.
  --output [OUTPUT], -o [OUTPUT]
  --list-variables, --list, -l
                        List available template variables
```
