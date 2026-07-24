# Copyright (c) 2026 João Paulo Silva Plöger.
#
# This software is provided "as is", without warranty of any kind, express or implied.
# Licensed under the [Apache License 2.0].
# See the LICENSE file in the project root for the complete terms.

import os
import sys
import locale
from pathlib import Path
from gooey import Gooey, GooeyParser

# Import the compressor classes from pyfcomp
from pyfcomp import PDFCompressor, ImageCompressor, VideoCompressor, ZipCompressor

# Absolute path to local languages folder containing translations
BASE_DIR = Path(__file__).resolve().parent
LOCAL_LANGUAGES = os.path.join(BASE_DIR, "languages")

def get_system_language() -> str:
    """Detects system locale and returns 'portuguese', 'german', or 'english'."""
    try:
        loc, _ = locale.getdefaultlocale()
        if loc:
            loc = loc.lower()
            if loc.startswith("pt"):
                return "portuguese"
            elif loc.startswith("de"):
                return "german"
    except Exception:
        pass
    return "english"

# Detect language and load UI strings
LANG = get_system_language()

STRINGS = {
    "portuguese": {
        "title": "Python File Compressor",
        "desc": "Compressor de arquivos PDF, Imagens, Vídeos e ZIP",
        "parser_desc": "Configure as opções de compressão abaixo:",
        "input_label": "Arquivo de Entrada",
        "input_help": "Selecione o arquivo que deseja comprimir (PDF, Imagem, Vídeo ou ZIP).",
        "output_label": "Caminho de Saída (Opcional)",
        "output_help": "Escolha onde salvar o arquivo. Se vazio, salvará na mesma pasta com o sufixo '_comprimido'.",
        "rate_label": "Taxa de Compressão",
        "rate_help": "Escolha o nível de compressão de 0 a 5 (0: mínima, 5: máxima. Padrão: 3).",
        "grayscale_label": "Remover Cores (Preto e Branco)?",
        "grayscale_help": "Se marcado, converte imagens (em PDFs ou avulsas) para tons de cinza.",
        "yes_label": "Sobrescrever Arquivo Existente?",
        "yes_help": "Se marcado, substitui o arquivo no destino sem avisar.",
        "error_exists": "ERRO: O arquivo '{}' já existe no diretório de destino.\nMarque a opção 'Sobrescrever o arquivo de saída' ou mude o caminho de destino.",
        "error_format": "ERRO: Formato de arquivo não suportado: '{}'"
    },
    "german": {
        "title": "Python Datei-Kompressor",
        "desc": "Komprimiert PDF-Dateien, Bilder, Videos und ZIP-Archive",
        "parser_desc": "Konfigurieren Sie die Komprimierungsoptionen unten:",
        "input_label": "Eingabedatei",
        "input_help": "Wählen Sie die zu komprimierende Datei (PDF, Bild, Video oder ZIP).",
        "output_label": "Ausgabepfad (Optional)",
        "output_help": "Wählen Sie, wo die Datei gespeichert werden soll. Wenn leer, wird sie im selben Ordner mit dem Suffix '_comprimido' gespeichert.",
        "rate_label": "Komprimierungsrate",
        "rate_help": "Wählen Sie die Komprimierungsrate von 0 bis 5 (0: Minimum, 5: Maximum. Standard: 3).",
        "grayscale_label": "Farben entfernen (Graustufen)?",
        "grayscale_help": "Wenn aktiviert, werden Bilder (in PDFs oder einzeln) in Graustufen konvertiert.",
        "yes_label": "Existierende Datei überschreiben?",
        "yes_help": "Wenn aktiviert, wird die Datei am Zielort ohne Warnung überschrieben.",
        "error_exists": "FEHLER: Die Datei '{}' existiert bereits im Zielverzeichnis.\nAktivieren Sie die Option 'Existierende Datei überschreiben' oder ändern Sie den Zielpfad.",
        "error_format": "FEHLER: Nicht unterstütztes Dateiformat: '{}'"
    },
    "english": {
        "title": "Python File Compressor",
        "desc": "Compresses PDF, Image, Video, and ZIP files",
        "parser_desc": "Configure the compression options below:",
        "input_label": "Input File",
        "input_help": "Select the file you want to compress (PDF, Image, Video, or ZIP).",
        "output_label": "Output Path (Optional)",
        "output_help": "Choose where to save the file. If empty, saves in the same folder with '_comprimido' suffix.",
        "rate_label": "Compression Rate",
        "rate_help": "Choose the compression rate from 0 to 5 (0: minimum, 5: maximum. Default: 3).",
        "grayscale_label": "Remove Colors (Grayscale)?",
        "grayscale_help": "If checked, converts images (in PDFs or standalone) to grayscale.",
        "yes_label": "Overwrite Existing File?",
        "yes_help": "If checked, overwrites the file in the destination without warning.",
        "error_exists": "ERROR: The file '{}' already exists in the destination directory.\nCheck 'Overwrite Existing File?' or change the output path.",
        "error_format": "ERROR: Unsupported file format: '{}'"
    }
}

S = STRINGS[LANG]

@Gooey(
    program_name=S["title"],
    program_description=S["desc"],
    default_size=(600, 720),
    language=LANG,
    language_dir=LOCAL_LANGUAGES,
    show_sidebar=False,
    disable_sidebar=True,
    show_failure_modal=False
)
def main():
    parser = GooeyParser(description=S["parser_desc"])

    # Files selection group
    files_group = parser.add_argument_group(S["input_label"])
    files_group.add_argument(
        "input_file",
        type=Path,
        metavar=S["input_label"],
        help=S["input_help"],
        widget="FileChooser"
    )
    files_group.add_argument(
        "-o", "--output",
        type=Path,
        required=False,
        metavar=S["output_label"],
        help=S["output_help"],
        widget="FileSaver"
    )

    # Options group
    options_group = parser.add_argument_group(S["rate_label"])
    options_group.add_argument(
        "-r", "--rate",
        type=int,
        choices=range(0, 6),
        default=3,
        metavar=S["rate_label"],
        help=S["rate_help"]
    )
    options_group.add_argument(
        "-g", "--grayscale",
        action="store_true",
        metavar=S["grayscale_label"],
        help=S["grayscale_help"]
    )
    options_group.add_argument(
        "-y", "--yes",
        action="store_true",
        metavar=S["yes_label"],
        help=S["yes_help"]
    )

    args = parser.parse_args()

    input_file: Path = args.input_file
    rate: int = args.rate
    grayscale: bool = args.grayscale
    
    suffix = input_file.suffix.lower()
    
    # Resolving default suffix name
    output_file = args.output
    if not output_file or str(output_file).strip() in ("", "."):
        output_file = input_file.with_name(f"{input_file.stem}_comprimido{suffix}")
    else:
        if output_file.suffix.lower() != suffix:
            output_file = output_file.with_suffix(suffix)

    # Check for overwrite
    if output_file.exists() and not args.yes and output_file != input_file:
        print(S["error_exists"].format(output_file.name), file=sys.stderr)
        sys.exit(1)

    # Route execution based on extension
    if suffix == ".pdf":
        PDFCompressor.compress(input_file, output_file, rate, grayscale)
    elif suffix in (".png", ".jpg", ".jpeg", ".webp"):
        ImageCompressor.compress(input_file, output_file, rate, grayscale)
    elif suffix in (".mp4", ".mkv", ".avi", ".mov"):
        VideoCompressor.compress(input_file, output_file, rate)
    elif suffix == ".zip":
        ZipCompressor.compress(input_file, output_file, rate)
    else:
        print(S["error_format"].format(suffix), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
