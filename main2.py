from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

app = FastAPI(title="API Simulada - Agente Rolcar (Demo)")

# ==========================================
# 0. CONFIGURACIÓN DE SEGURIDAD (API KEY)
# ==========================================
API_KEY_NAME = "X-API-Key"
API_KEY_SECRETA = "rolcar_agente_2026_secreto" 
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def validar_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY_SECRETA:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Acceso denegado: API Key inválida o faltante"
    )

# ==========================================
# 1. NUESTRA BASE DE DATOS FALSA (EN MEMORIA)
# ==========================================
PRODUCTOS_DB = [
    {"codigo_interno": "02AB005", "nombre": "BUJIA NISSAN TSURU II 1.6 L", "precio": 43.28},
    {"codigo_interno": "02AB011", "nombre": "BUJIA FORD TOPAZ 2.3 L", "precio": 31.90},
    {"codigo_interno": "02BU120", "nombre": "ACEITE SINTETICO MOTOR 5W30", "precio": 250.00},
    {"codigo_interno": "02BU019", "nombre": "FILTRO DE AIRE CHEVROLET CAVALIER", "precio": 120.50},
    {"codigo_interno": "02BU094", "nombre": "BALATAS DELANTERAS NISSAN VERSA", "precio": 450.00}
]

carrito_actual = {
    "id_orden": "ORD-0001",
    "estado": "abierto", 
    "items": []
}

# ==========================================
# 2. MODELOS DE DATOS
# ==========================================
class ItemCarrito(BaseModel):
    codigo_interno: str
    cantidad: int = 1

# ==========================================
# 3. ENDPOINTS PARA EL AGENTE DE IA
# ==========================================

# A. Listar todos los productos (Catálogo)
@app.get("/api/v1/productos/lista")
def listar_nombres_productos(api_key: str = Depends(validar_api_key)):
    nombres = [prod["nombre"] for prod in PRODUCTOS_DB]
    return {
        "status": "success",
        "total": len(nombres),
        "productos_disponibles": nombres
    }

# B. Buscar Productos Específicos
@app.get("/api/v1/productos/buscar")
def buscar_productos(query: str = "", api_key: str = Depends(validar_api_key)):
    resultados = []
    for prod in PRODUCTOS_DB:
        if query.lower() in prod["nombre"].lower() or query.lower() in prod["codigo_interno"].lower():
            resultados.append(prod)
    return {
        "status": "success",
        "query": query,
        "total": len(resultados),
        "data": resultados
    }

# C. Ver el Carrito Actual
@app.get("/api/v1/carrito")
def ver_carrito(api_key: str = Depends(validar_api_key)):
    total = sum(item["precio"] * item["cantidad"] for item in carrito_actual["items"])
    return {
        "carrito": carrito_actual,
        "total_pagar": round(total, 2)
    }

# D. Agregar al carrito
@app.post("/api/v1/carrito/agregar")
def agregar_producto(item: ItemCarrito, api_key: str = Depends(validar_api_key)):
    if carrito_actual["estado"] == "cerrado":
        raise HTTPException(status_code=400, detail="La orden ya está cerrada. Crea un nuevo carrito.")
        
    producto = next((p for p in PRODUCTOS_DB if p["codigo_interno"] == item.codigo_interno), None)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    carrito_actual["items"].append({
        "codigo_interno": producto["codigo_interno"],
        "nombre": producto["nombre"],
        "precio": producto["precio"],
        "cantidad": item.cantidad
    })
    return {"status": "success", "mensaje": f"Agregaste {item.cantidad}x {producto['nombre']} al carrito."}

# E. Quitar del carrito
@app.delete("/api/v1/carrito/quitar/{codigo_interno}")
def quitar_producto(codigo_interno: str, api_key: str = Depends(validar_api_key)):
    global carrito_actual
    items_filtrados = [item for item in carrito_actual["items"] if item["codigo_interno"] != codigo_interno]
    if len(items_filtrados) == len(carrito_actual["items"]):
        raise HTTPException(status_code=404, detail="El producto no estaba en el carrito")
        
    carrito_actual["items"] = items_filtrados
    return {"status": "success", "mensaje": "Producto removido del carrito"}

# F. Cerrar la Orden / Checkout
@app.post("/api/v1/carrito/cerrar")
def cerrar_orden(api_key: str = Depends(validar_api_key)):
    if not carrito_actual["items"]:
        raise HTTPException(status_code=400, detail="El carrito está vacío, no se puede cerrar la orden.")
        
    carrito_actual["estado"] = "cerrado"
    total = sum(item["precio"] * item["cantidad"] for item in carrito_actual["items"])
    
    return {
        "status": "success", 
        "mensaje": f"¡Orden {carrito_actual['id_orden']} cerrada exitosamente!",
        "total_cobrado": round(total, 2)
    }
