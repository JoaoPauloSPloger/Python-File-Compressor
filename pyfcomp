# Copyright (c) 2026 João Paulo Silva Plöger.
#
# This software is provided "as is", without warranty of any kind, express or implied.
# Licensed under the [Apache License 2.0].
# See the LICENSE file in the project root for the complete terms.
import sys

import argparse
import time
import io
import logging
from pathlib import Path
from typing import Optional, Dict

import fitz  # PyMuPDF
from PIL import Image

# Logging configuration for production-level outputs
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PDFCompressor:
    """Handles PDF compression using PyMuPDF and Pillow."""
    
    # Configuration dictionary replaces the original 'if/elif' chain
    COMPRESSION_PROFILES = {
        3: {"max_dim": 1500, "jpeg_quality": 75, "garbage": 4, "deflate": True, "clean": True},
        4: {"max_dim": 1000, "jpeg_quality": 50, "garbage": 4, "deflate": True, "clean": True},
        5: {"max_dim": 600,  "jpeg_quality": 25, "garbage": 4, "deflate": True, "clean": True},
    }

    @staticmethod
    def get_file_size(path: Path) -> int:
        """Returns the file size in bytes."""
        try:
            return path.stat().st_size
        except OSError:
            return 0

    @staticmethod
    def format_size(size_bytes: float) -> str:
        """Formats bytes into a human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    @classmethod
    def _compress_image(cls, image_bytes: bytes, image_ext: str, max_dim: int, jpeg_quality: int) -> Optional[bytes]:
        """Processes and compresses a single image stream. Returns compressed bytes or None."""
        try:
            # Using context manager to ensure safe resource disposal
            with Image.open(io.BytesIO(image_bytes)) as img:
                width, height = img.size
                needs_resize = width > max_dim or height > max_dim
                
                if not (needs_resize or image_ext.lower() in ["png", "jpeg", "jpg"]):
                    return None
                    
                if needs_resize:
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                    
                has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
                
                out_io = io.BytesIO()
                if has_alpha:
                    img.save(out_io, format="PNG", optimize=True)
                else:
                    img.convert("RGB").save(out_io, format="JPEG", quality=jpeg_quality)
                    
                compressed_data = out_io.getvalue()
                return compressed_data if len(compressed_data) < len(image_bytes) else None
        except Exception as e:
            logger.debug(f"Image processing failed: {e}")
            return None

    @classmethod
    def compress(cls, input_path: Path, output_path: Path, rate: int) -> None:
        """Main orchestration method for PDF compression."""
        if not input_path.exists():
            logger.error(f"File not found: '{input_path}'")
            sys.exit(1)
            
        start_time = time.time()
        initial_size = cls.get_file_size(input_path)
        
        logger.info(f"Opening: {input_path} ({cls.format_size(initial_size)})")
        
        try:
            doc = fitz.open(input_path)
        except Exception as e:
            logger.error(f"Failed to open PDF: {e}")
            sys.exit(1)
            
        total_pages = len(doc)
        logger.info(f"Pages: {total_pages} | Target Compression Rate: {rate}/5")
        
        compress_images = rate >= 3
        profile = cls.COMPRESSION_PROFILES.get(rate, {})
        
        if compress_images and profile:
            logger.info("Compressing document images. This might take a moment...")
            processed_xrefs: Dict[int, int] = {}
            
            for page_num in range(total_pages):
                page = doc[page_num]
                for img_info in page.get_images(full=True):
                    xref = img_info[0]
                    if xref in processed_xrefs:
                        continue
                        
                    try:
                        base_image = doc.extract_image(xref)
                        if not base_image:
                            continue
                            
                        compressed_data = cls._compress_image(
                            base_image["image"], 
                            base_image["ext"], 
                            profile["max_dim"], 
                            profile["jpeg_quality"]
                        )
                        
                        if compressed_data:
                            page.replace_image(xref, stream=compressed_data)
                            processed_xrefs[xref] = len(compressed_data)
                        else:
                            processed_xrefs[xref] = len(base_image["image"])
                            
                    except Exception as e:
                        logger.debug(f"Failed to process xref {xref}: {e}")
                        processed_xrefs[xref] = 0
        
        # Configure object deletion options based on compression rate
        garbage_level = profile.get("garbage", 1) if rate >= 3 else (2 if rate == 1 else (3 if rate == 2 else 1))
        deflate_val = profile.get("deflate", False) if rate >= 3 else (True if rate in (1, 2) else False)
        clean_val = profile.get("clean", False) if rate >= 3 else (True if rate == 2 else False)
        
        logger.info("Saving compressed PDF...")
        temp_output = output_path.with_suffix('.tmp') if output_path == input_path else output_path
        
        try:
            doc.save(
                str(temp_output),
                garbage=garbage_level,
                deflate=deflate_val,
                clean=clean_val
            )
        except Exception as e:
            logger.error(f"Failed to save PDF: {e}")
            if temp_output.exists():
                temp_output.unlink(missing_ok=True)
            sys.exit(1)
        finally:
            # Ensures memory is freed even if an exception occurs
            doc.close()
            
        if output_path == input_path and temp_output.exists():
            temp_output.replace(output_path)
            
        final_size = cls.get_file_size(output_path)
        elapsed_time = time.time() - start_time
        saved_bytes = initial_size - final_size
        percent_saved = (saved_bytes / initial_size) * 100 if initial_size > 0 else 0
        
        logger.info("=" * 55)
        logger.info("COMPRESSION COMPLETED SUCCESSFULLY")
        logger.info(f"Output File:  {output_path}")
        logger.info(f"Initial Size: {cls.format_size(initial_size)}")
        logger.info(f"Final Size:   {cls.format_size(final_size)}")
        logger.info(f"Space Saved:  {cls.format_size(saved_bytes)} ({percent_saved:.2f}%)")
        logger.info(f"Time Elapsed: {elapsed_time:.2f} seconds")
        logger.info("=" * 55)

def main():
    parser = argparse.ArgumentParser(
        prog="pyfcomp.py", 
        description="Compresses PDF files using PyMuPDF and Pillow."
    )
    
    parser.add_argument("input_pdf", type=Path, help="Path to the input PDF file.")
    parser.add_argument("-r", "--rate", type=int, choices=range(0, 6), default=3,
                        help="Compression rate from 0 to 5 (0: minimum, 5: maximum. Default: 3).")
    parser.add_argument("-o", "--output", type=Path, help="Path to the output PDF file (optional).")
    parser.add_argument("-y", "--yes", action="store_true", help="Overwrite the output file without prompting.")
    
    args = parser.parse_args()
    
    input_pdf: Path = args.input_pdf
    rate: int = args.rate
    
    output_pdf: Path = args.output if args.output else input_pdf.with_name(f"{input_pdf.stem}_compressed{input_pdf.suffix}")
        
    if output_pdf.exists() and not args.yes and output_pdf != input_pdf:
        resp = input(f"The output file '{output_pdf}' already exists. Overwrite? (y/n): ").strip().lower()
        if resp not in ["y", "yes"]:
            logger.info("Operation cancelled by the user.")
            sys.exit(0)
            
    PDFCompressor.compress(input_pdf, output_pdf, rate)

if __name__ == "__main__":
    main()
