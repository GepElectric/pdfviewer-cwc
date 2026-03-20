# Module Template Memory

## Purpose

`ModuleTemplate` je pocetni skeleton za novi `WinCC Unified Companion` modul.

Cilj template-a je da novi modul odmah prati Companion host logiku:

- host discovery preko `modules/<module_id>/module.json`
- start/stop/restart iz hosta
- `open_main_window`
- `get_status`
- `shutdown`
- mogucnost standalone pokretanja
- mogucnost buildanja u `.exe`


## Mental Model

Companion sustav ima 2 nivoa:

1. `Host`
   - cita `modules/*/module.json`
   - provjerava postoji li entrypoint
   - pokrece modul kao zaseban proces
   - preko named pipe salje komandne requeste

2. `Module`
   - ima vlastiti process
   - sam otvara svoj glavni prozor
   - sam drzi svoj runtime state
   - odgovara hostu na:
     - `open_main_window`
     - `get_status`
     - `shutdown`


## Minimalni Ugovor Modula

Da bi host prepoznao i koristio modul, modul mora imati:

- `module.json`
- entrypoint koji host moze pokrenuti
- command server koji zna obraditi:
  - `open_main_window`
  - `get_status`
  - `shutdown`

Prakticno:

- `open_main_window`
  - fokusira ili otvara glavni prozor modula
- `get_status`
  - vraca JSON-like status payload
- `shutdown`
  - pokrece uredno gasenje modula


## Source Layout

Template koristi ovaj layout:

```text
ModuleTemplate/
  README.md
  MODULE_TEMPLATE_MEMORY.md
  module.json
  requirements.txt
  build_module_exe.bat
  hosted_runtime.py
  main.py
  example_module/
    __init__.py
    app.py
```

Kad radis novi modul, tipicno:

1. kopiras `ModuleTemplate`
2. preimenujes folder
3. preimenujes `example_module` package
4. uredis `module.json`
5. popunis `app.py` business logikom


## EXE Layout

Kad modul buildas kao `PyInstaller --onedir`, host-ready paket modula treba izgledati ovako:

```text
modules/
  example_module/
    module.json
    ExampleModule/
      ExampleModule.exe
      _internal/
```

Za host je to dovoljno ako je build ispravno spakirao sav Python kod i assete.

Build skripta bi trebala izbaciti oba artefakta:

- `dist/<module_package>/`
- `dist/<module_package>.zip`

ZIP treba imati isti root sadrzaj kao finalni `modules/<id>/` folder, tako da ga host moze direktno instalirati preko `Install Module`.


## Sto ide u module.json

Template `module.json` pokazuje na `.exe` build layout jer je to produkcijski cilj:

- `entrypoint`: `ExampleModule/ExampleModule.exe`
- `working_dir`: `ExampleModule`

Ako zelis prvo testirati source varijantu, privremeno mozes staviti:

- `entrypoint`: `main.py`
- `working_dir`: `.`


## Runtime Args

Host modulima dodaje ove argumente:

- `--hosted`
- `--module-id`
- `--config-dir`
- `--data-dir`
- `--log-dir`
- `--command-pipe`
- `--host-instance-id`

Modul ih mora znati primiti bez pucanja.

Template to rjesava u `hosted_runtime.py`.


## Status Payload

`get_status` ne mora biti kompleksan, ali treba vratiti barem:

- `status`
- `ui_ready`
- `module_id`
- `version`

Pozeljno:

- `last_error`
- `config_dir`
- `data_dir`
- `log_dir`


## Standalone vs Hosted

Template podrzava 2 moda:

1. standalone
   - pokreces `python main.py`
   - otvori se modul UI

2. hosted
   - host pokrene modul s runtime argumentima
   - modul registrira command pipe
   - host ga moze kontrolirati


## Build Strategy

Preporuceni build za novi modul:

- `PyInstaller`
- `--windowed`
- `--onedir`

Razlog:

- lakse debugiranje
- manje problema s assetima
- prirodno za Companion module package layout


## Ako modul treba dodatne assete

Ako modul koristi:

- fontove
- ikonice
- logo fajlove
- default JSON configove
- HTML/CSS/JS assete

onda ih treba:

1. drzati lokalno unutar modula
2. dodati u PyInstaller build preko `--add-data`


## Companion Core

Template namjerno ne ovisi o vanjskom `companion_core` folderu.

Umjesto toga ima lokalni `hosted_runtime.py` koji daje minimalni Companion runtime ugovor.

To olaksava:

- novi modul
- standalone razvoj
- manje copy/paste zavisnosti


## Recommended Workflow For New Module

1. kopiraj `ModuleTemplate`
2. promijeni:
   - folder name
   - `module.json`
   - exe name u `build_module_exe.bat`
   - package name `example_module`
3. implementiraj UI i business logiku u `example_module/app.py`
4. testiraj source mode
5. buildaj `.exe`
6. kopiraj gotovi paket u host `modules/<module_id>/`
7. ili iskoristi `dist/<module_package>.zip` kroz host `Install Module`
8. u hostu klikni `Refresh` samo ako si radio rucni copy


## Production Checklist

Prije drop-in testa u host:

- `module.json` postoji
- `entrypoint` pokazuje na stvarni `.exe`
- `working_dir` je tocan
- modul odgovara na `get_status`
- `open_main_window` radi
- `shutdown` radi
- asseti su ugradeni u build


## Practical Rule

Ako novi modul ne znas kako zapoceti, kreni ovako:

- UI ide u `example_module/app.py`
- Companion runtime ide kroz `main.py` + `hosted_runtime.py`
- build ide kroz `build_module_exe.bat`
- host metadata ide u `module.json`
