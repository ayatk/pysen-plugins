# pysen-plugins

A plugin for running tools in pysen that are not included in pysen.

https://github.com/pfnet/pysen/tree/main/examples/plugin_example

## autoflake

https://github.com/myint/autoflake

> autoflake removes unused imports and unused variables from Python code.

I have specified `format` as the target, so when I run` pysen run format`, it runs with it.

### Settings

```toml
[tool.pysen.plugin.autoflake]
script = "path/to/autoflake.py"

[tool.pysen.plugin.autoflake.config]
includes = ["."]
excludes = [".venv"]
imports = ["django", "requests", "urllib3"]
# expand wildcard star imports with undefined names
# default: false
expand_star_imports = false
# remove all unused variables
# default: false
remove_unused_variables = false
# exclude __init__.py when removing unused imports
# default: false
ignore_init_module_imports = false
# remove all duplicate keys in objects
# default: false
remove_duplicate_keys = false
# remove all unused imports
# default: false
remove_all_unused_imports = false
```
