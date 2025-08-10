import numpy as np
from PIL import Image
from typing import List, Optional
import io

# InsightFace heavy imports are delayed to first use to speed startup
_face_app = None

def _lazy_app():
    global _face_app
    if _face_app is None:
        from insightface.app import FaceAnalysis
        _face_app = FaceAnalysis(name="buffalo_l")  # downloads on first use
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
    return _face_app

def image_bytes_to_rgb(image_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return img

def get_face_embedding(image_bytes: bytes) -> Optional[List[float]]:
    """Return a 512-dim embedding using InsightFace or None if no face."""
    img = image_bytes_to_rgb(image_bytes)
    app = _lazy_app()
    faces = app.get(np.asarray(img))
    if not faces:
        return None
    # Use the largest detected face
    face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
    emb = face.normed_embedding  # already L2-normalized
    return emb.astype(float).tolist()

def cosine_similarity(a: List[float], b: List[float]) -> float:
    a = np.asarray(a); b = np.asarray(b)
    # vectors expected to be normalized; similarity in [-1,1], higher is better
    return float(np.dot(a, b))
