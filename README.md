
# Templateer

```
usage: templateer.py [-h] --template [TEMPLATE]
                     (--output [OUTPUT] | --list-variables)

Simple pure-Python, dependency-free template processor.

Template variables are surrounded by `@@`. Template variables can be passed
in the environment:

    VAR1=foo templateer -t example-with-var1.txt -o output.txt

If not provided in the environment, templateer will prompt the user for values.

options:
  -h, --help            show this help message and exit
  --template [TEMPLATE], -t [TEMPLATE]
  --output [OUTPUT], -o [OUTPUT]
  --list-variables, --list, -l
                        List available template variables

```
