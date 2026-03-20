# PDF Module Template

Ovo je prilagodeni template za `WinCC Unified Companion` PDF modul.

Template je napravljen tako da novi modul moze raditi:

- standalone
- kao hosted Companion modul
- kao `.exe` modul za host `modules/` folder

## Pocetak

1. Kopiraj ovaj folder
2. Media Module koristi:
   - package folder `media_module`
   - EXE name `MediaModule`
   - module id `media_module`
3. PDF logika i localhost server su u:
   - `media_module/app.py`
   - `media_module/pdf_server.py`
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
- `media_module/app.py`
  - UI i PDF open logic
- `media_module/pdf_server.py`
  - lokalni PDF HTTP server za lokalne disk putanje
- `module.json`
  - host manifest
- `build_module_exe.bat`
  - PyInstaller build skripta + host-installable package output

Detaljnije u:

- `MODULE_TEMPLATE_MEMORY.md`
