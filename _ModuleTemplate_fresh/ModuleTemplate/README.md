# Module Template

Ovo je pocetni template za novi `WinCC Unified Companion` modul.

Template je napravljen tako da novi modul moze raditi:

- standalone
- kao hosted Companion modul
- kao `.exe` modul za host `modules/` folder

## Pocetak

1. Kopiraj ovaj folder
2. Promijeni nazive:
   - `example_module`
   - `ExampleModule`
   - `example_module` u `module.json`
3. Implementiraj UI i logiku u `example_module/app.py`
4. Testiraj:

```powershell
python main.py
```

5. Buildaj:

```powershell
.\build_module_exe.bat
```

6. Kopiraj gotovi paket u host:

```text
modules/<your_module_id>/
```

Ili jos jednostavnije:

- uzmi `dist/<package_name>.zip`
- u hostu klikni `Install Module`

## Bitni fajlovi

- `main.py`
  - hosted + standalone entrypoint
- `hosted_runtime.py`
  - minimalni Companion runtime helper
- `example_module/app.py`
  - UI i business logika
- `module.json`
  - host manifest
- `build_module_exe.bat`
  - PyInstaller build skripta + host-installable package output

Detaljnije u:

- `MODULE_TEMPLATE_MEMORY.md`
