from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="API Simulada - Agente Rolcar (Demo)")

# ==========================================
# 1. NUESTRA BASE DE DATOS FALTAL (EN MEMORIA)
# ==========================================
PRODUCTOS_DB = [
    {"codigo_interno": "02AB005", "nombre": "BUJIA NISSAN TSURU II 1.6 L", "precio": 43.28},
    {"codigo_interno": "02AB011", "nombre": "BUJIA FORD TOPAZ 2.3 L", "precio": 31.90},
    {"codigo_interno": "02BU120", "nombre": "ACEITE SINTETICO MOTOR 5W30", "precio": 250.00},
    {"codigo_interno": "02BU019", "nombre": "FILTRO DE AIRE CHEVROLET CAVALIER", "precio": 120.50},
    {"codigo_interno": "02BU094", "nombre": "BALATAS DELANTERAS NISSAN VERSA", "precio": 450.00}
]

# Simularemos un carrito guardándolo en una variable global
carrito_actual = {
    "id_orden": "ORD-0001",
    "estado": "abierto", # Puede ser "abierto" o "cerrado"
    "items": []
}

# ==========================================
# 2. MODELOS DE DATOS (Lo que el Agente nos envía)
# ==========================================
class ItemCarrito(BaseModel):
    codigo_interno: str
    cantidad: int = 1

# ==========================================
# 3. ENDPOINTS PARA EL AGENTE DE IA
# ==========================================

# A. Buscar Productos (El Agente usará esto para ver qué hay)
@app.get("/api/v1/productos/buscar")
def buscar_productos(query: str = ""):
    resultados = []
    # Buscamos coincidencias ignorando mayúsculas y minúsculas
    for prod in PRODUCTOS_DB:
        if query.lower() in prod["nombre"].lower() or query.lower() in prod["codigo_interno"].lower():
            resultados.append(prod)
            
    return {
        "status": "success",
        "query": query,
        "total": len(resultados),
        "data": resultados
    }

# B. Ver el Carrito Actual
@app.get("/api/v1/carrito")
def ver_carrito():
    total = sum(item["precio"] * item["cantidad"] for item in carrito_actual["items"])
    return {
        "carrito": carrito_actual,
        "total_pagar": round(total, 2)
    }

# C. Agregar al carrito
@app.post("/api/v1/carrito/agregar")
def agregar_producto(item: ItemCarrito):
    if carrito_actual["estado"] == "cerrado":
        raise HTTPException(status_code=400, detail="La orden ya está cerrada. Crea un nuevo carrito.")
        
    # Buscamos si el producto existe en nuestra BD falsa
    producto = next((p for p in PRODUCTOS_DB if p["codigo_interno"] == item.codigo_interno), None)
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    # Agregamos al carrito
    carrito_actual["items"].append({
        "codigo_interno": producto["codigo_interno"],
        "nombre": producto["nombre"],
        "precio": producto["precio"],
        "cantidad": item.cantidad
    })
    
    return {"status": "success", "mensaje": f"Agregaste {item.cantidad}x {producto['nombre']} al carrito."}

# D. Quitar del carrito
@app.delete("/api/v1/carrito/quitar/{codigo_interno}")
def quitar_producto(codigo_interno: str):
    global carrito_actual
    # Filtramos el carrito para dejar todos menos el que queremos borrar
    items_filtrados = [item for item in carrito_actual["items"] if item["codigo_interno"] != codigo_interno]
    
    if len(items_filtrados) == len(carrito_actual["items"]):
        raise HTTPException(status_code=404, detail="El producto no estaba en el carrito")
        
    carrito_actual["items"] = items_filtrados
    return {"status": "success", "mensaje": "Producto removido del carrito"}

# E. Cerrar la Orden (Checkout)
@app.post("/api/v1/carrito/cerrar")
def cerrar_orden():
    if not carrito_actual["items"]:
        raise HTTPException(status_code=400, detail="El carrito está vacío, no se puede cerrar la orden.")
        
    carrito_actual["estado"] = "cerrado"
    total = sum(item["precio"] * item["cantidad"] for item in carrito_actual["items"])
    
    # Aquí en un sistema real, guardaríamos esto en BD y limpiaríamos el carrito
    return {
        "status": "success", 
        "mensaje": f"¡Orden {carrito_actual['id_orden']} cerrada exitosamente!",
        "total_cobrado": round(total, 2)
    }
# F. Listar todos los productos (Solo nombres para el catálogo)
@app.get("/api/v1/productos/lista")
def listar_nombres_productos(api_key: str = Depends(validar_api_key)):
    # Usamos list comprehension para extraer solo el campo "nombre" de cada producto
    nombres = [prod["nombre"] for prod in PRODUCTOS_DB]
    
    return {
        "status": "success",
        "total": len(nombres),
        "productos_disponibles": nombres
    }
