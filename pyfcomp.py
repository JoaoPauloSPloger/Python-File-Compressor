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
    def _compress_image(cls, image_bytes: bytes, image_ext: str, max_dim: int, jpeg_quality: int, grayscale: bool = False) -> Optional[bytes]:
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
                
                # Apply grayscale conversion if requested
                if grayscale:
                    img = img.convert("LA" if has_alpha else "L")
                
                out_io = io.BytesIO()
                if has_alpha:
                    img.save(out_io, format="PNG", optimize=True)
                else:
                    save_img = img if img.mode == "L" else img.convert("RGB")
                    save_img.save(out_io, format="JPEG", quality=jpeg_quality)
                    
                compressed_data = out_io.getvalue()
                return compressed_data if len(compressed_data) < len(image_bytes) else None
        except Exception as e:
            logger.debug(f"Image processing failed: {e}")
            return None

    @classmethod
    def compress(cls, input_path: Path, output_path: Path, rate: int, grayscale: bool = False) -> None:
        """Main orchestration method for PDF compression."""
        if not input_path.exists():
            logger.error(f"File not found: '{input_path}'")
            sys.exit(1)
            
        start_time = time.time()
        initial_size = cls.get_file_size(input_path)
        
        logger.info(f"Opening PDF: {input_path} ({cls.format_size(initial_size)})")
        
        try:
            doc = fitz.open(input_path)
        except Exception as e:
            logger.error(f"Failed to open PDF: {e}")
            sys.exit(1)
            
        total_pages = len(doc)
        logger.info(f"Pages: {total_pages} | Target Compression Rate: {rate}/5")
        
        compress_images = rate >= 3
        profile = cls.COMPRESSION_PROFILES.get(rate, {})
        
        if (compress_images and profile) or grayscale:
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
                            
                        # If rate < 3 but grayscale is requested, use placeholder dimensions/quality
                        max_dim = profile.get("max_dim", 99999)
                        jpeg_quality = profile.get("jpeg_quality", 90)
                        
                        compressed_data = cls._compress_image(
                            base_image["image"], 
                            base_image["ext"], 
                            max_dim, 
                            jpeg_quality,
                            grayscale=grayscale
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
        logger.info("PDF COMPRESSION COMPLETED SUCCESSFULLY")
        logger.info(f"Output File:  {output_path}")
        logger.info(f"Initial Size: {cls.format_size(initial_size)}")
        logger.info(f"Final Size:   {cls.format_size(final_size)}")
        logger.info(f"Space Saved:  {cls.format_size(saved_bytes)} ({percent_saved:.2f}%)")
        logger.info(f"Time Elapsed: {elapsed_time:.2f} seconds")
        logger.info("=" * 55)


class ImageCompressor:
    """Handles image compression (JPEG, PNG, WEBP) using Pillow."""
    
    COMPRESSION_PROFILES = {
        3: {"max_dim": 1920, "jpeg_quality": 80},
        4: {"max_dim": 1280, "jpeg_quality": 60},
        5: {"max_dim": 800,  "jpeg_quality": 40},
    }

    @classmethod
    def compress(cls, input_path: Path, output_path: Path, rate: int, grayscale: bool = False) -> None:
        if not input_path.exists():
            logger.error(f"File not found: '{input_path}'")
            sys.exit(1)

        start_time = time.time()
        initial_size = PDFCompressor.get_file_size(input_path)
        logger.info(f"Opening image: {input_path} ({PDFCompressor.format_size(initial_size)})")

        try:
            with Image.open(input_path) as img:
                fmt = img.format if img.format else input_path.suffix[1:].upper()
                if fmt == "MPO":
                    fmt = "JPEG"
                
                # Check alpha channel
                has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)

                # Convert to grayscale if requested
                if grayscale:
                    img = img.convert("LA" if has_alpha else "L")

                # Resize if rate >= 3
                profile = cls.COMPRESSION_PROFILES.get(rate, {})
                if rate >= 3 and profile:
                    max_dim = profile["max_dim"]
                    width, height = img.size
                    if width > max_dim or height > max_dim:
                        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

                # Prepare output saving kwargs
                save_kwargs = {}
                if fmt in ("JPEG", "JPG"):
                    save_kwargs["quality"] = profile.get("jpeg_quality", 85) if rate >= 3 else 95
                    save_kwargs["optimize"] = True
                    # If it has alpha but we want to save as JPEG, convert it to RGB/L
                    if img.mode in ("RGBA", "LA"):
                        img = img.convert("L" if grayscale else "RGB")
                elif fmt == "WEBP":
                    save_kwargs["quality"] = profile.get("jpeg_quality", 80) if rate >= 3 else 90
                elif fmt == "PNG":
                    save_kwargs["optimize"] = True

                # If output is same as input, write to temp then replace
                temp_output = output_path.with_suffix('.tmp') if output_path == input_path else output_path
                img.save(temp_output, format=fmt, **save_kwargs)
                
                if output_path == input_path and temp_output.exists():
                    temp_output.replace(output_path)

        except Exception as e:
            logger.error(f"Failed to compress image: {e}")
            sys.exit(1)

        final_size = PDFCompressor.get_file_size(output_path)
        elapsed_time = time.time() - start_time
        saved_bytes = initial_size - final_size
        percent_saved = (saved_bytes / initial_size) * 100 if initial_size > 0 else 0

        logger.info("=" * 55)
        logger.info("IMAGE COMPRESSION COMPLETED SUCCESSFULLY")
        logger.info(f"Output File:  {output_path}")
        logger.info(f"Initial Size: {PDFCompressor.format_size(initial_size)}")
        logger.info(f"Final Size:   {PDFCompressor.format_size(final_size)}")
        logger.info(f"Space Saved:  {PDFCompressor.format_size(saved_bytes)} ({percent_saved:.2f}%)")
        logger.info(f"Time Elapsed: {elapsed_time:.2f} seconds")
        logger.info("=" * 55)


class VideoCompressor:
    """Handles video compression using FFmpeg subprocess calls."""
    
    COMPRESSION_PROFILES = {
        0: {"crf": 18, "audio_bitrate": "192k", "max_height": None},
        1: {"crf": 20, "audio_bitrate": "192k", "max_height": None},
        2: {"crf": 22, "audio_bitrate": "160k", "max_height": None},
        3: {"crf": 26, "audio_bitrate": "128k", "max_height": 1080},
        4: {"crf": 30, "audio_bitrate": "96k",  "max_height": 720},
        5: {"crf": 35, "audio_bitrate": "64k",  "max_height": 480},
    }

    @classmethod
    def compress(cls, input_path: Path, output_path: Path, rate: int) -> None:
        if not input_path.exists():
            logger.error(f"File not found: '{input_path}'")
            sys.exit(1)
            
        import shutil
        if not shutil.which("ffmpeg"):
            logger.error("FFmpeg not found in PATH. Video compression requires FFmpeg.")
            sys.exit(1)

        start_time = time.time()
        initial_size = PDFCompressor.get_file_size(input_path)
        logger.info(f"Opening video: {input_path} ({PDFCompressor.format_size(initial_size)})")

        profile = cls.COMPRESSION_PROFILES.get(rate, cls.COMPRESSION_PROFILES[3])
        temp_output = output_path.with_suffix('.tmp') if output_path == input_path else output_path

        import subprocess
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-vcodec", "libx264",
            "-crf", str(profile["crf"]),
            "-preset", "medium",
            "-acodec", "aac",
            "-b:a", profile["audio_bitrate"]
        ]

        # Aspect ratio aware scaling to max height (ensuring width is divisible by 2 for H264)
        max_height = profile["max_height"]
        if max_height:
            cmd.extend(["-vf", f"scale=-2:{max_height}"])

        cmd.append(str(temp_output))

        try:
            logger.info("Running video transcoding via FFmpeg. This may take a while...")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed (code {result.returncode}): {result.stderr.splitlines()[-1] if result.stderr.splitlines() else ''}")
                
            if output_path == input_path and temp_output.exists():
                temp_output.replace(output_path)

        except Exception as e:
            logger.error(f"Failed to compress video: {e}")
            if temp_output.exists() and temp_output != output_path:
                temp_output.unlink(missing_ok=True)
            sys.exit(1)

        final_size = PDFCompressor.get_file_size(output_path)
        elapsed_time = time.time() - start_time
        saved_bytes = initial_size - final_size
        percent_saved = (saved_bytes / initial_size) * 100 if initial_size > 0 else 0

        logger.info("=" * 55)
        logger.info("VIDEO COMPRESSION COMPLETED SUCCESSFULLY")
        logger.info(f"Output File:  {output_path}")
        logger.info(f"Initial Size: {PDFCompressor.format_size(initial_size)}")
        logger.info(f"Final Size:   {PDFCompressor.format_size(final_size)}")
        logger.info(f"Space Saved:  {PDFCompressor.format_size(saved_bytes)} ({percent_saved:.2f}%)")
        logger.info(f"Time Elapsed: {elapsed_time:.2f} seconds")
        logger.info("=" * 55)


class ZipCompressor:
    """Handles ZIP archive re-compression using maximum DEFLATE level."""

    @classmethod
    def compress(cls, input_path: Path, output_path: Path, rate: int) -> None:
        if not input_path.exists():
            logger.error(f"File not found: '{input_path}'")
            sys.exit(1)

        start_time = time.time()
        initial_size = PDFCompressor.get_file_size(input_path)
        logger.info(f"Opening ZIP archive: {input_path} ({PDFCompressor.format_size(initial_size)})")

        import zipfile
        # Map 0-5 compression rate to 1-9 DEFLATE level
        compress_level = max(1, min(9, int(rate * 1.8))) if rate > 0 else 1
        temp_output = output_path.with_suffix('.tmp') if output_path == input_path else output_path

        try:
            logger.info(f"Re-packing archive contents with compression level {compress_level}...")
            with zipfile.ZipFile(input_path, 'r') as in_zip:
                with zipfile.ZipFile(temp_output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compress_level) as out_zip:
                    for item in in_zip.infolist():
                        data = in_zip.read(item.filename)
                        out_zip.writestr(item, data)
                        
            if output_path == input_path and temp_output.exists():
                temp_output.replace(output_path)

        except Exception as e:
            logger.error(f"Failed to compress ZIP archive: {e}")
            if temp_output.exists() and temp_output != output_path:
                temp_output.unlink(missing_ok=True)
            sys.exit(1)

        final_size = PDFCompressor.get_file_size(output_path)
        elapsed_time = time.time() - start_time
        saved_bytes = initial_size - final_size
        percent_saved = (saved_bytes / initial_size) * 100 if initial_size > 0 else 0

        logger.info("=" * 55)
        logger.info("ZIP COMPRESSION COMPLETED SUCCESSFULLY")
        logger.info(f"Output File:  {output_path}")
        logger.info(f"Initial Size: {PDFCompressor.format_size(initial_size)}")
        logger.info(f"Final Size:   {PDFCompressor.format_size(final_size)}")
        logger.info(f"Space Saved:  {PDFCompressor.format_size(saved_bytes)} ({percent_saved:.2f}%)")
        logger.info(f"Time Elapsed: {elapsed_time:.2f} seconds")
        logger.info("=" * 55)


def main():
    parser = argparse.ArgumentParser(
        prog="pyfcomp.py", 
        description="Compresses PDF, Image, Video, and ZIP files."
    )
    
    parser.add_argument("input_file", type=Path, help="Path to the input file.")
    parser.add_argument("-r", "--rate", type=int, choices=range(0, 6), default=3,
                        help="Compression rate from 0 to 5 (0: minimum, 5: maximum. Default: 3).")
    parser.add_argument("-o", "--output", type=Path, help="Path to the output file (optional).")
    parser.add_argument("-y", "--yes", action="store_true", help="Overwrite the output file without prompting.")
    parser.add_argument("-g", "--grayscale", action="store_true", help="Remove color from images (PDF and standalone images only).")
    
    args = parser.parse_args()
    
    input_file: Path = args.input_file
    rate: int = args.rate
    grayscale: bool = args.grayscale
    
    suffix = input_file.suffix.lower()
    
    output_file: Path = args.output if args.output else input_file.with_name(f"{input_file.stem}_compressed{suffix}")
        
    if output_file.exists() and not args.yes and output_file != input_file:
        resp = input(f"The output file '{output_file}' already exists. Overwrite? (y/n): ").strip().lower()
        if resp not in ["y", "yes"]:
            logger.info("Operation cancelled by the user.")
            sys.exit(0)
            
    if suffix == ".pdf":
        PDFCompressor.compress(input_file, output_file, rate, grayscale)
    elif suffix in (".png", ".jpg", ".jpeg", ".webp"):
        ImageCompressor.compress(input_file, output_file, rate, grayscale)
    elif suffix in (".mp4", ".mkv", ".avi", ".mov"):
        VideoCompressor.compress(input_file, output_file, rate)
    elif suffix == ".zip":
        ZipCompressor.compress(input_file, output_file, rate)
    else:
        logger.error(f"Unsupported file format: '{suffix}'")
        sys.exit(1)

if __name__ == "__main__":
    main()
