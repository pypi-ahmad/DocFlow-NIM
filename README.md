# DocFlow NIM

DocFlow NIM converts PDF pages and images into structured text using NVIDIA Nemotron-3.5-Parse. Choose local GPU inference or NVIDIA's hosted service in the Streamlit interface. The app is a work in progress.

## Start

Follow the [first-time setup](docs/user-guide.md#first-time-setup), then run `launch.cmd` and open [http://127.0.0.1:8472](http://127.0.0.1:8472). The launcher starts the local worker even when you intend to use online mode.

- [User guide](docs/user-guide.md): setup, conversion, downloads, and troubleshooting.
- [Developer guide](docs/developer-guide.md): architecture, files, and checks.
- [Model research](docs/nemotron-3.5-parse-research.md): sources and deployment context.

## Current capabilities

The app supports PDF, PNG, JPEG, GIF, TIFF, and WebP uploads, single-file page selection, sequential multi-file conversion, annotated page previews, Markdown and JSON downloads, and saved ZIP exports. New conversions also generate HTML and chunk files for the ZIP. Office inputs, concurrent batches, additional exports, a conversion CLI, and a public conversion API are unfinished. Chat, classification, and business-field extraction are excluded. The app uses neither OpenAI models nor PP-DocLayoutV3.

## Clone

Repository: [pypi-ahmad/DocFlow-NIM](https://github.com/pypi-ahmad/DocFlow-NIM)

```powershell
git clone https://github.com/pypi-ahmad/DocFlow-NIM.git
cd DocFlow-NIM
```
