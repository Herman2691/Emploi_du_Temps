# utils/storage.py — stockage local (développement local sans Supabase Storage)
import uuid
import os
import base64

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
COURSE_DOCS_BUCKET    = "course-docs"
TP_SUBMISSIONS_BUCKET = "tp-submissions"
ANNOUNCEMENTS_BUCKET  = "announcements"
UNIVERSITY_LOGOS_BUCKET = "university-logos"

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
_MIME_MAP   = {
    ".pdf":  "application/pdf",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".gif":  "image/gif",
    ".webp": "image/webp",
    ".bmp":  "image/bmp",
}


def _mime(filename: str) -> str:
    ext = os.path.splitext(filename.lower())[1]
    return _MIME_MAP.get(ext, "application/octet-stream")


def is_image(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] in _IMAGE_EXTS


def upload_file(file_bytes: bytes, original_name: str,
                bucket: str, folder: str = "") -> tuple:
    """Sauvegarde un fichier (PDF ou image) localement.
    Conserve l'extension d'origine. Retourne (stored_path, stored_path).
    """
    parts = [UPLOADS_DIR, bucket]
    if folder:
        parts.append(folder)
    os.makedirs(os.path.join(*parts), exist_ok=True)

    ext         = os.path.splitext(original_name.lower())[1] or ".bin"
    filename    = f"{uuid.uuid4()}{ext}"
    stored_path = "/".join(filter(None, [bucket, folder, filename]))
    full_path   = os.path.join(UPLOADS_DIR, *stored_path.split("/"))

    with open(full_path, "wb") as f:
        f.write(file_bytes)

    return stored_path, stored_path


def upload_pdf(file_bytes: bytes, original_name: str,
               bucket: str, folder: str = "") -> tuple:
    """Alias conservé pour compatibilité — délègue à upload_file."""
    return upload_file(file_bytes, original_name, bucket, folder)


def get_file_bytes(stored_path: str) -> bytes | None:
    full_path = os.path.join(UPLOADS_DIR, *stored_path.split("/"))
    if not os.path.exists(full_path):
        return None
    with open(full_path, "rb") as f:
        return f.read()


def get_file_base64(stored_path: str) -> str | None:
    """Retourne un data URI base64 (PDF ou image) pour affichage inline."""
    data = get_file_bytes(stored_path)
    if data is None:
        return None
    mime = _mime(stored_path)
    return f"data:{mime};base64," + base64.b64encode(data).decode()


# Alias PDF maintenus pour compatibilité
def get_pdf_bytes(stored_path: str) -> bytes | None:
    return get_file_bytes(stored_path)


def get_pdf_base64(stored_path: str) -> str | None:
    return get_file_base64(stored_path)


def delete_file(stored_path: str, bucket: str = "") -> None:
    try:
        full_path = os.path.join(UPLOADS_DIR, *stored_path.split("/"))
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception:
        pass
