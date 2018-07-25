## FPEAM Graphic User Interface

> Currently this interface only supports the creation and editing of configuration files.

### Set-up dependencies

```bash
python -m venv fpeam

# On Mac/Linux:
source fpeam/bin/activate
# On Windows:
call fpeam\scripts\activate.bat

pip install -r requirements.txt
```

### Run and Compile
```bash
# Run app:
python -m fbs run

# Build app:
python -m fbs freeze
```

Once compiled the executable can be found inside `target` folder.