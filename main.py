from fastapi import FastAPI, Query
from pydantic import BaseModel
import pandas as pd
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajusta esto según tu configuración de seguridad
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_FILE = 'anuncios.csv'

# Ensure the CSV file exists
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=['id', 'titulo', 'descripcion', 'fecha']).to_csv(CSV_FILE, index=False)

def read_csv():
    return pd.read_csv(CSV_FILE)

def write_csv(df):
    df.to_csv(CSV_FILE, index=False)

class Anuncio(BaseModel):
    titulo: str
    descripcion: str
    fecha: str

@app.get("/anuncios")
async def get_anuncios(page: int = Query(1, ge=1), size: int = Query(4, ge=1)):
    df = read_csv()
    start = (page - 1) * size
    end = start + size
    anuncios = df.iloc[start:end]
    # Convertir id a int para evitar problemas de serialización
    anuncios['id'] = anuncios['id'].astype(int)
    return anuncios.to_dict(orient='records')

@app.post("/anuncios")
async def create_anuncio(anuncio: Anuncio):
    df = read_csv()
    new_id = df['id'].max() + 1 if not df.empty else 1
    anuncio_dict = anuncio.dict()
    anuncio_dict['id'] = int(new_id)  # Convertir a int
    new_row = pd.DataFrame([anuncio_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    write_csv(df)
    return anuncio_dict

@app.put("/anuncios/{anuncio_id}")
async def update_anuncio(anuncio_id: int, anuncio: Anuncio):
    df = read_csv()
    if anuncio_id in df['id'].values:
        df.loc[df['id'] == anuncio_id, ['titulo', 'descripcion', 'fecha']] = [anuncio.titulo, anuncio.descripcion, anuncio.fecha]
        write_csv(df)
        return {"msg": "Anuncio actualizado"}
    else:
        return {"msg": "Anuncio no encontrado"}, 404

@app.delete("/anuncios/{anuncio_id}")
async def delete_anuncio(anuncio_id: int):
    df = read_csv()
    if anuncio_id in df['id'].values:
        df = df[df['id'] != anuncio_id]
        write_csv(df)
        return {"msg": "Anuncio eliminado"}
    else:
        return {"msg": "Anuncio no encontrado"}, 404

# Cargar el archivo CSV en un DataFrame de pandas
df = pd.read_csv("anuncios.csv")

@app.get("/anuncios")
async def get_anuncios(page: int = Query(1, gt=0)):
    per_page = 4
    start = (page - 1) * per_page
    end = start + per_page

    # Obtener los anuncios para la página actual
    anuncios_paginados = df.iloc[start:end].to_dict(orient="records")

    # Calcular el número total de páginas
    total_pages = (len(df) + per_page - 1) // per_page

    return {
        "anuncios": anuncios_paginados,
        "totalPages": total_pages
    }

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os



# Configurar la ruta para servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ruta para subir archivos
@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    file_location = f"static/images/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    return {"filename": file.filename}

# Ruta para listar las imágenes
@app.get("/images/")
async def list_images():
    images_dir = "static/images"
    images = [f"http://localhost:8000/static/images/{img}" for img in os.listdir(images_dir)]
    return images

# Ruta para eliminar imágenes
@app.delete("/images/{image_name}")
async def delete_image(image_name: str):
    file_path = f"static/images/{image_name}"
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"detail": "Image deleted"}
    raise HTTPException(status_code=404, detail="Image not found")
