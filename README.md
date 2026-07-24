# ⚡ Python File Compressor (pyfcomp)

A robust, modern, and highly efficient file compression tool. Originally designed under the Unix philosophy of simplicity and specialization, **pyfcomp** has evolved into a complete multi-format compressor, offering both a command-line interface (CLI) and a user-friendly, auto-localized graphical user interface (GUI).

---

## 🚀 Current Features

* **Smart Multi-Format Compression:**
  * **PDF:** Optimizes internal structures (removes duplicate objects, compresses fonts, and metadata) and optionally reduces the size of internal embedded images.
  * **Images:** Supports `.png`, `.jpg`, `.jpeg`, `.webp`, applying smart resizing and quality compression profiles.
  * **Videos:** Automatic transcoding to H.264 (MP4/MKV/AVI/MOV) via **FFmpeg**, with fine-grained control over audio bitrate, visual quality (CRF), and resolution.
  * **ZIP:** Re-compresses `.zip` files using the maximum efficiency of the DEFLATE algorithm (level 9).
* **Color Removal (Grayscale):** Option to convert images (standalone or embedded in PDFs) to black and white (grayscale), further reducing file size for scanned documents and text-heavy files.
* **Multilingual Graphical Interface (GUI):** A modern native interface (built with Gooey) that **automatically detects the operating system's language** (supporting Portuguese, German, and English) and translates all menus, dialog buttons, and error warnings.
* **Smart Routing:** The system automatically detects the input file type and routes it to the correct compressor algorithm, requiring zero user configuration.

---

## 📊 Compression Level Matrix

The system maps compression rates from **0** (minimum aggressiveness) to **5** (maximum space saving) custom-tailored per format:

| Format | Level 0 | Level 1 | Level 2 | Level 3 (Default) | Level 4 | Level 5 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PDF** | Basic structural rewriting | Light structural optimization | Strong structural optimization | Images at 1500px, Quality 75% | Images at 1000px, Quality 50% | Images at 600px, Quality 25% |
| **Images** | Basic file optimization | Basic file optimization | Basic file optimization | Resizing to 1920px, Quality 80% | Resizing to 1280px, Quality 60% | Resizing to 800px, Quality 40% |
| **Videos** | High fidelity (CRF 18), Audio 192k | Very high quality (CRF 20), Audio 192k | High quality (CRF 22), Audio 160k | Medium quality (CRF 26), 1080p, Audio 128k | Moderate quality (CRF 30), 720p, Audio 96k | Maximum compression quality (CRF 35), 480p, Audio 64k |
| **ZIP** | DEFLATE Level 1 | DEFLATE Level 1 | DEFLATE Level 3 | DEFLATE Level 5 | DEFLATE Level 7 | DEFLATE Level 9 (Maximum) |

---

## 🛠️ Prerequisites

1. **Python Dependencies:**
   Using a virtual environment (venv) is highly recommended.
   ```bash
   pip install -r requirements.txt
   ```

2. **System Tool (FFmpeg):**
   * **Video** compression requires **FFmpeg** to be installed on your operating system and added to your `PATH`.
   * If FFmpeg is not detected when attempting to compress a video, the application will display a clear and safe warning error.

---

## 💻 How to Use

### 1. Graphical Interface (GUI) - Recommended for manual usage

Start the multilingual visual window:
```bash
python gui.py
```

### 2. Command Line Interface (CLI) - Recommended for automation

Base syntax:
```bash
python pyfcomp.py <file_path> [options]
```

#### CLI Parameters and Options:
* `input_file`: Path to the file you want to compress (PDF, Image, Video, or ZIP).
* `-r, --rate`: Compression level from `0` to `5`. Default is `3`.
* `-o, --output`: Destination path. If empty, the file will be saved in the same folder as the original with a `_compressed` suffix (or `_comprimido` in the PT GUI).
* `-y, --yes`: Overwrites the output file silently if it already exists.
* `-g, --grayscale`: Converts images/PDFs to grayscale (Black and White).

#### CLI Usage Examples:

* **Standard Image compression (Level 3):**
  ```bash
  python pyfcomp.py photo.png
  ```

* **Aggressive Video compression (Level 4) with custom output:**
  ```bash
  python pyfcomp.py recording.mp4 -r 4 -o /path/to/optimized_video.mp4
  ```

* **Color removal in PDF (Grayscale) with extreme rate (Level 5):**
  ```bash
  python pyfcomp.py document.pdf -r 5 -g -y
  ```

---

## 🔮 Future Roadmap

* **Batch Compression:** Support for selecting entire directories and compressing multiple files in a queue simultaneously in both GUI and CLI.
* **Native Multithreading:** Internal parallel execution to compress PDF pages or multiple files from the queue.
* **Smart Size Validation:** If the final compressed file is larger than the original, the system will automatically revert to the original to save bytes and prevent data bloating.

---

## 📄 License

Copyright (c) 2026 João Paulo Silva Plöger.

This software is distributed under the terms of the **Apache License 2.0**. See the `LICENSE` file for more details.
