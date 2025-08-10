from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import timedelta
import os, json, uuid, shutil

from database import SessionLocal, init_db, Employee, Punch
from auth import create_access_token, authenticate_user
from face import get_face_embedding, cosine_similarity

# --- App setup ---
app = FastAPI(title="Ponto-AI (MVP)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PHOTOS_DIR = os.getenv("PHOTOS_DIR", "data/photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize DB
init_db()

# --- Schemas ---
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class EmployeeOut(BaseModel):
    id: int
    name: str
    document: Optional[str] = None
    email: Optional[str] = None
    class Config:
        from_attributes = True

class PunchOut(BaseModel):
    id: int
    employee_id: int
    similarity: Optional[float] = None
    class Config:
        from_attributes = True

# --- Auth ---
@app.post("/auth/login", response_model=TokenResponse)
def login(username: str = Form(...), password: str = Form(...)):
    if not authenticate_user(username, password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": username}, expires_delta=timedelta(hours=12))
    return TokenResponse(access_token=token)

# --- Employee enrollment ---
@app.post("/employees", response_model=EmployeeOut)
async def create_employee(
    name: str = Form(...),
    document: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    selfie: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    img_bytes = await selfie.read()
    emb = get_face_embedding(img_bytes)
    if emb is None:
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado na selfie.")
    # save selfie
    file_id = f"{uuid.uuid4().hex}.jpg"
    photo_path = os.path.join(PHOTOS_DIR, file_id)
    with open(photo_path, "wb") as f:
        f.write(img_bytes)
    emp = Employee(name=name, document=document, email=email,
                   face_embedding=json.dumps(emb), photo_path=photo_path)
    db.add(emp); db.commit(); db.refresh(emp)
    return emp

@app.post("/faces/enroll/{employee_id}", response_model=EmployeeOut)
async def re_enroll(employee_id: int, selfie: UploadFile = File(...), db: Session = Depends(get_db)):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    img_bytes = await selfie.read()
    emb = get_face_embedding(img_bytes)
    if emb is None:
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado na selfie.")
    file_id = f"{uuid.uuid4().hex}.jpg"
    photo_path = os.path.join(PHOTOS_DIR, file_id)
    with open(photo_path, "wb") as f:
        f.write(img_bytes)
    emp.face_embedding = json.dumps(emb)
    emp.photo_path = photo_path
    db.add(emp); db.commit(); db.refresh(emp)
    return emp

# --- Punch-in/out ---
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.80"))  # higher is stricter

@app.post("/punches", response_model=PunchOut)
async def punch(
    employee_id: int = Form(...),
    lat: Optional[float] = Form(None),
    lon: Optional[float] = Form(None),
    selfie: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    img_bytes = await selfie.read()
    emb = get_face_embedding(img_bytes)
    if emb is None:
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado na selfie.")

    enrolled = json.loads(emp.face_embedding) if emp.face_embedding else None
    if enrolled is None:
        raise HTTPException(status_code=400, detail="Funcionário sem cadastro facial.")

    sim = cosine_similarity(emb, enrolled)

    file_id = f"{uuid.uuid4().hex}.jpg"
    photo_path = os.path.join(PHOTOS_DIR, file_id)
    with open(photo_path, "wb") as f:
        f.write(img_bytes)

    punch = Punch(employee_id=employee_id, lat=lat, lon=lon, similarity=sim, photo_path=photo_path)
    db.add(punch); db.commit(); db.refresh(punch)

    if sim < SIMILARITY_THRESHOLD:
        # Not a hard failure: record saved for auditoria, but return 400 to app
        raise HTTPException(status_code=400, detail=f"Reconhecimento facial falhou (similaridade={sim:.2f}).")

    return punch

@app.get("/employees", response_model=List[EmployeeOut])
def list_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()

@app.get("/punches/export.csv")
def export_csv(db: Session = Depends(get_db)):
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id","employee_id","ts","lat","lon","similarity","photo_path"])
    for p in db.query(Punch).order_by(Punch.id):
        writer.writerow([p.id, p.employee_id, p.ts.isoformat(), p.lat, p.lon, p.similarity, p.photo_path])
    return output.getvalue()
