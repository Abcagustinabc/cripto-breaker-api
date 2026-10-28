"""
API web del Cripto Breaker (version 3.0).
Sirve la interfaz visual (index.html) y expone los endpoints JSON.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from cripto_breaker import (
    romper_automatico,
    detectar_tipo_inteligente,
    MIN_LETRAS_VIGENERE,
    MIN_LETRAS_SUSTITUCION,
    MIN_LETRAS_CESAR,
)

app = FastAPI(
    title="Cripto Breaker API",
    description="Rompe cifrados clásicos: César, Vigenère, sustitución simple y XOR.",
    version="3.0.0",
)


class TextoCifrado(BaseModel):
    texto: str
    tipo: str | None = None


@app.get("/")
async def raiz():
    """Devuelve la interfaz visual web."""
    return FileResponse("index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/info")
async def info():
    """Devuelve informacion sobre minimos de texto para cada cifrado."""
    return {
        "min_letras_cesar": MIN_LETRAS_CESAR,
        "min_letras_vigenere": MIN_LETRAS_VIGENERE,
        "min_letras_sustitucion": MIN_LETRAS_SUSTITUCION,
        "notas": {
            "vigenere": "Funciona mejor con 200+ letras.",
            "sustitucion": "Funciona mejor con 150+ letras.",
            "cesar": "Funciona desde 5 letras.",
            "xor": "Necesita 50+ bytes.",
        },
    }


@app.post("/romper")
async def romper(datos: TextoCifrado):
    if not datos.texto or not datos.texto.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacio.")

    if datos.tipo and datos.tipo not in ("cesar", "vigenere", "sustitucion", "xor"):
        raise HTTPException(
            status_code=400,
            detail=f"Tipo no valido: '{datos.tipo}'. Usa: cesar, vigenere, sustitucion, xor o deja vacio."
        )

    try:
        resultado = romper_automatico(datos.texto, tipo=datos.tipo, verbose=False)

        if resultado.get("metodo") == "ERROR":
            raise HTTPException(
                status_code=400,
                detail=resultado.get("error", "Error desconocido")
            )

        respuesta = {
            "exito": True,
            "metodo_detectado": resultado.get("metodo"),
            "texto_descifrado": resultado.get("texto", ""),
            "score": resultado.get("score", 0),
            "detalles": {
                k: v for k, v in resultado.items()
                if k not in ("texto", "metodo", "score", "mapeo", "clave", "advertencia")
            },
        }
        if "advertencia" in resultado:
            respuesta["advertencia"] = resultado["advertencia"]

        return respuesta

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.post("/detectar")
async def detectar(datos: TextoCifrado):
    if not datos.texto or not datos.texto.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacio.")

    try:
        tipo, score, detalle = detectar_tipo_inteligente(datos.texto, verbose=False)
        if tipo is None:
            raise HTTPException(status_code=400, detail=detalle)
        return {
            "exito": True,
            "tipo_detectado": tipo,
            "score": score,
            "detalle": detalle,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")