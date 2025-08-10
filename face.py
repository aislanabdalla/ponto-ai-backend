import numpy as np
from PIL import Image
from typing import List, Optional
import io

# Mantemos um objeto global para não recarregar o modelo a cada chamada
_face_app = None

def _lazy_app():
    global _face_app
    if _face_app is None:
        from insightface.app import FaceAnalysis
        # Modelo pequeno + CPU + apenas módulos necessários = menos RAM
        _face_app = FaceAnalysis(
            name="buffalo_sc",
            providers=["CPUExecutionProvider"],
            allowed_modules=["detection", "recognition"],
        )
        # Janela de detecção menor também economiza memória
        _face_app.prepare(ctx_id=0, det_size=(320, 320))
    return _face_app

def image_bytes_to_rgb(image_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return img

def get_face_embedding(image_bytes: bytes) -> Optional[List[float]]:
    """Gera o embedding (lista de floats) do maior rosto encontrado."""
    img = image_bytes_to_rgb(image_bytes)
    app = _lazy_app()
    faces = app.get(np.asarray(img))
    if not faces:
        return None
    # maior rosto
    face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
    emb = face.normed_embedding  # já normalizado (L2)
    return emb.astype(float).tolist()

def cosine_similarity(a: List[float], b: List[float]) -> float:
    a = np.asarray(a)
    b = np.asarray(b)
    return float(np.dot(a, b))
