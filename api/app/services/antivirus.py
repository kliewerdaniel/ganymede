# Ganymede API — Antivirus Service

"""ClamAV virus scanning via clamdscan."""

import logging
import shutil
import subprocess
from typing import Tuple

logger = logging.getLogger(__name__)


def scan_file(file_path: str) -> Tuple[bool, str]:
    """
    Scan a file for viruses using clamdscan.
    Returns (is_clean, message).
    """
    # Check if clamdscan is available
    if not shutil.which("clamdscan"):
        logger.warning("clamdscan not available, skipping virus scan")
        return True, "No virus scanner available"

    try:
        import subprocess
        result = subprocess.run(
            ["clamdscan", "--no-summary", file_path],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # clamdscan returns 0 if clean, 1 if virus found
        if result.returncode == 0:
            return True, "Clean"
        elif result.returncode == 1:
            return False, f"Virus found: {result.stdout.strip()}"
        else:
            return False, f"Scan error: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return False, "Scan timeout"
    except Exception as e:
        logger.error(f"Virus scan failed: {e}")
        return False, f"Scan failed: {str(e)}"
