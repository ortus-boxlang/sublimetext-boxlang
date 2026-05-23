# BoxLang Sublime Text Package — Test Fixtures

This directory contains sample files used by the test suite.

## Fixture Files

| File | Purpose |
|------|---------|
| `sample_class.bx` | Sample `.bx` class file for parser tests |
| `sample_script.bxs` | Sample `.bxs` script file for parser tests |
| `sample_module.bxm` | Sample `.bxm` module file for parser tests |

## Usage

Fixtures are loaded by tests using the `fixture_path` fixture from `conftest.py`:

```python
def test_parse_fixture_file(fixture_path):
    file = os.path.join(fixture_path, "sample_class.bx")
    # ... test code
```
