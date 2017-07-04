# Contributing

Recommended way to get started is to create and activate a project virtual environment.

You should ensure you are using a supported Python version, you can check the .travis.yml to see which versions we use for CI.

* [Pythonz](https://github.com/saghul/pythonz#installation) can be used to install a specific Python version.
* [Virtualenvwrapper](http://virtualenvwrapper.readthedocs.io/en/latest/install.html#basic-installation) can help setting up and managing virtualenvs

## Quickstart

```bash
$ python --version
Python 3.6.1
$ make install
$ make test
```
## Tests
Tests are executed by running `$ make test`, but can also be executed by running:
   * `$ py.test tests` for all tests
   
       or
   * `$ py.test tests/test_clearmash_api.py` (**example**) to run the specific single test 'test_clearmash_api.py'.

## Configuration

Some pipelines have settings, we use .env file for that, just copy .env.example into .env and modify according to your needs

## See Also

To run the full datapackage-pipelines environment you should use Docker, see [README-DOCKER](README-DOCKER.md) for more details.
