# PdfViewer / MediaViewer CWC

[![Repo](https://img.shields.io/badge/GitHub-pdfviewer--cwc-24292f?logo=github)](https://github.com/GepElectric/pdfviewer-cwc)
[![Release](https://img.shields.io/github/v/release/GepElectric/pdfviewer-cwc)](https://github.com/GepElectric/pdfviewer-cwc/releases)

`PdfViewer` is a WinCC Unified Custom Web Control that evolved into a media browser and viewer for PDFs, images, audio, and video, with a local helper backend.

## Repository Contents

- `deploy_cwc.bat`: builds and copies the CWC ZIP to the WinCC `CustomControls` folder
- `{A1B7F3B4-FD9F-40A0-80FC-69C20AE48E4B}/`: CWC manifest and frontend assets
- `pdf_local_server.ps1`: local media helper
- `start_media_local_server.bat`: starts the active media helper
- `start_pdf_local_server.bat`: compatibility wrapper
- `_ModuleTemplate_extract/`: active module packaging source
- `_ModuleTemplate_fresh/`: clean template-derived reference copy
- `MediaModule.zip`: built module package

## What It Does

- browses files from a configured root folder
- previews PDF, image, audio, and video content
- restores the last selected item when configured
- supports custom PDF viewing behavior and navigation state
- serves local files through a localhost helper

## Local Development

1. Start the helper with `start_media_local_server.bat`
2. Deploy the CWC with `deploy_cwc.bat`
3. Reload the WinCC screen or reimport the control if needed

## Notes

- local media access depends on the localhost helper being active
- module artifacts are built from the template extract folder
- extra template ZIPs and build outputs are intentionally ignored by git
