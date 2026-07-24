
A rigorous and scalable command-line utility (CLI) for file compression. Designed on the traditional principles of UNIX tools, **pyfcomp** focuses on efficiency, data safety, and optimized computational resource processing.

Currently, the processing core features native and deep support for **PDF** files (via `PyMuPDF` and `Pillow`). The modular and object-oriented architecture was structured. Multiple file extensions and formats will be implemented in future iterations.

## Current Features
- **Profile-Driven PDF Compression:** 6 compression levels (0 to 5). The engine dynamically adjusts the image resolution threshold, JPEG quantization quality, and the file's defragmentation level (garbage collection).
- **Traditional CLI:** Clean, predictable, and parameterizable terminal interface.


## Prerequisites
The allocation of a virtual environment (venv) is recommended to prevent system library poisoning.
```bash
pip install PyMuPDF Pillow
```

## Usage (CLI)

The base syntax follows the consolidated and non-negotiable standard of POSIX systems:

```bash
python pyfcomp.py <input_file> [options]

```

### Arguments and Options

* `input_file`: Explicit path to the original file.
* `-r, --rate`: Compression level from `0` (minimum) to `5` (maximum aggressiveness). Default is `3`.
* `-o, --output`: Path to the output file. If omitted, the system appends the `_compressed` suffix to the original name.
* `-y, --yes`: Security bypass. Silently overwrites the output file, ignoring terminal confirmation prompts.

### Operation Examples

Standard compression (Level 3):

```bash
python pyfcomp.py document.pdf

```

Maximum compression (Level 5) with a specific output file and forced overwrite:

```bash
python pyfcomp.py research_report.pdf -r 5 -o optimized_research_report.pdf -y

```

## Visionary Roadmap

The code's foundation abandons linear execution in favor of class encapsulation (`PDFCompressor`). It paves the way for independent modules. The logical expansion plan includes:

* Parallel compression algorithms for raw and lossless images (PNG, WEBP).
* Structural minification for text files, raw databases, and exported logs.
* Post-compression cryptographic integrity checking (hash validation) to ensure zero loss of critical metadata.

## License and Authorship

Copyright (c) 2026 João Paulo Silva Plöger.

This software is provided "as is", without warranty of any kind, express or implied.
Licensed under the **Apache License 2.0**.
See the `LICENSE` file in the project root for the complete terms.
