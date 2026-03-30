from pathlib import Path
import zipfile
import subprocess
import platform

# Pure-Python streaming ZIP reader (no central directory)
try:
    from stream_unzip import stream_unzip
except Exception:
    stream_unzip = None
try:
    import py7zr
except Exception:
    py7zr = None


def unzip_files(src_path: Path, dst_path: Path) -> None:
    # Try ZIP next (most Aekta exports are ZIP even if extensionless)
    # 1) First attempt with stdlib zipfile (possibly patched with Deflate64)
    try:
        with zipfile.ZipFile(src_path, "r") as z:
            z.extractall(dst_path)
        print(f"\n------------ Extraction using: zipfile ------------\n")
        # print("Extraction with: zipfile")
        return
    except Exception:
        pass

    # 2) Try streaming unzip reader if available (handles missing central directory)
    if stream_unzip is not None:
        try:
            print(f"\n------------ Extraction using: stream_unzip ------------\n")
            # print("stream_unzip")
            with open(src_path, "rb") as f:
                for file_name, file_size, unzipped_chunks in stream_unzip(f):
                    # file_name is bytes per stream_unzip contract
                    out_path = dst_path / Path(file_name.decode("utf-8", errors="ignore"))
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(out_path, "wb") as w:
                        for chunk in unzipped_chunks:
                            w.write(chunk)
            return
        except Exception:
            pass

    # 3) try 7z if available and looks like 7z
    if py7zr is not None:
        try:
            if hasattr(py7zr, "is_7zfile") and py7zr.is_7zfile(src_path):
                print(f"\n------------ Extraction using: py7zr ------------\n")
                # print("py7zr")
                with py7zr.SevenZipFile(src_path, "r") as z:
                    z.extractall(dst_path)
                return
        except Exception:
            # Fall through to other formats
            pass

    # 4) macOS fallback to ditto for stubborn archives
    try:
        if platform.system().lower() == 'darwin':
            print(f"\n------------ Extraction using: ditto (only on macOS) ------------\n")
            # print("Fallback to ditto (only on macOS)")
            subprocess.run(["ditto", "-xk", str(src_path), str(dst_path)], check=True)
            return
    except Exception:
        pass

    raise RuntimeError(f"Unsupported or unknown archive format: {src_path}")


if __name__ == "__main__":
    src = Path("./../docs/zip_files/HiTrap_run_1.zip")
    dst = Path("./../docs/unzipped_files/HiTrap_run_1")

    unzip_files(src, dst)
    print(f"------------ Extracted {src} → {dst} ------------\n")

    # unzip all Chrom.1_x_True directories in the parent directory
    parent_dir = Path("./../docs/unzipped_files/HiTrap_run_1/")
    for item in parent_dir.iterdir():
        # print(item)
        if item.name.startswith("Chrom.1_") and item.name.endswith("_True"):
            src = item
            dst = parent_dir / f"{item.name}_unzipped"
            unzip_files(src, dst)
            print(f"------------ Extracted {src} → {dst} ------------\n")
