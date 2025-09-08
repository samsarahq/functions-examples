# Guide to additional Python dependencies in Functions

Before bundling this template run:

```sh
python run-before-bundle/install_deps_to_lib.py
```

Then bundle as usual.

## How to add custom additional dependencies

Before running the setup script from above, add your dependencies to the `run-before-bundle/requirements.txt` file.

## Improve development experience

To get autocompletion for the extra packages in your editor, you can install the packages to your local Python enviroment:

```sh
pip install -r run-before-bundle/requirements.txt
```

Or add the generated `lib` folder to `python.analysis.extraPaths` if your editor supports that (e.g. VSCode, Cursor do).

## Getting `platform-warning` log in the install step

Using the default bundle built with this warning on production will cause the Function to fail with an import error.

In that case, to make a bundle that can work in production, but not locally, run install step with the `prod` arg.

```sh
python run-before-bundle/install_deps_to_lib.py prod
```

Then bundle, and use the output zip file in the Samsara dashboard instead of the locally working one.
