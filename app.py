"""
Juguetron API Proxy
API simple para búsqueda y sugerencias de productos de Juguetron.mx
Diseñado para Agentes de IA
"""

import base64
import json
import httpx
from typing import List, Optional
from enum import Enum
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Juguetron API",
    description="API para búsqueda de productos y servicios mock (Inventario, Pedidos, Soporte, Facturación) - Diseñado para Agentes de IA",
    version="1.1.0"
)

# Configurar CORS para agentes de IA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint for health checks"""
    return {"status": "ok", "service": "juguetron-api", "version": "1.1.0"}


# VTEX GraphQL Configuration
VTEX_BASE_URL = "https://www.juguetron.mx/_v/segment/graphql/v1"

# VTEX Persisted Query Hashes
AUTOCOMPLETE_HASH = "069177eb2c038ccb948b55ca406e13189adcb5addcb00c25a8400450d20e0108"
PRODUCT_SUGGESTIONS_HASH = "3eca26a431d4646a8bbce2644b78d3ca734bf8b4ba46afe4269621b64b0fb67d"


class Product(BaseModel):
    """Modelo de producto simplificado para Agentes de IA"""
    id: str
    name: str
    description: Optional[str] = None
    price: Optional[str] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None


class SearchResponse(BaseModel):
    """Modelo de respuesta unificado para Agents de IA"""
    query: str
    suggestions: List[str] = []
    products: List[Product] = []
    total_products: int = 0


class SearchRequest(BaseModel):
    """Modelo de solicitud para búsqueda (POST) - Compatible con Agentes de IA"""
    termino_busqueda: Optional[str] = None
    query: Optional[str] = None
    
    class Config:
        extra = "allow"  # Permitir campos adicionales


# ============================================================================
# MOCK API - Endpoints para Demostración
# ============================================================================

# B. Inventario (Híbrido)
class StockCheckRequest(BaseModel):
    """Request para verificación de stock"""
    sku: str
    zip_code: Optional[str] = None


class StockCheckResponse(BaseModel):
    """Respuesta de verificación de stock"""
    success: bool
    message: str
    stock: dict
    available_locations: List[dict]
    estimated_delivery: Optional[str] = None


# C. Pedidos (Mock Janis)
class OrderTrackingRequest(BaseModel):
    """Request para seguimiento de pedido"""
    order_id: str


class OrderTrackingResponse(BaseModel):
    """Respuesta de seguimiento de pedido"""
    order_id: str
    status: str
    estimated_delivery: str
    current_location: str
    last_update: str
    items: List[dict]
    tracking_number: str


# D. Soporte (Mock Zendesk)
class TicketCategory(str, Enum):
    """Categorías de tickets"""
    PRODUCTO_DANADO = "Producto Dañado"
    REEMBOLSO = "Reembolso"
    CAMBIO = "Cambio"
    GENERAL = "General"


class CreateTicketRequest(BaseModel):
    """Request para crear ticket"""
    email: str
    category: TicketCategory
    description: str
    sentiment: Optional[str] = None


class CreateTicketResponse(BaseModel):
    """Respuesta de creación de ticket"""
    success: bool
    ticket_id: str
    message: str
    priority: str
    estimated_response_time: str


# E. Admin (Mock ERP)
class InvoiceGenerationRequest(BaseModel):
    """Request para generación de factura"""
    order_id: str
    rfc: str


class InvoiceGenerationResponse(BaseModel):
    """Respuesta de generación de factura"""
    success: bool
    invoice_id: str
    pdf_url: str
    message: str
    total: str
    tax: str


# F. Facturación Juguetron (Mock del sistema SAT/CFDI)
class PaymentMethod(str, Enum):
    """Métodos de pago para facturación"""
    EFECTIVO = "Efectivo"
    TARJETA_DEBITO = "Tarjeta de Débito"
    TARJETA_CREDITO = "Tarjeta de Crédito"
    TRANSFERENCIA = "Transferencia electrónica de fondos"


class InvoiceCFDIRequest(BaseModel):
    """Request para facturación CFDI de Juguetron"""
    rfc: str
    ticket_number: str
    total: float
    payment_method: PaymentMethod
    
    class Config:
        extra = "allow"  # Permitir campos adicionales


class InvoiceCFDIResponse(BaseModel):
    """Respuesta de facturación CFDI"""
    success: bool
    message: str
    invoice_id: Optional[str] = None
    pdf_url: Optional[str] = None
    validation_errors: List[str] = []
    invoice_details: Optional[dict] = None


# HTTP client reutilizable
http_client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)


def encode_variables(variables: dict) -> str:
    """Codifica variables a base64"""
    return base64.b64encode(json.dumps(variables).encode('utf-8')).decode('utf-8')


def build_url(operation_name: str, hash_value: str, variables: dict) -> str:
    """Construye URL para VTEX GraphQL"""
    encoded_vars = encode_variables(variables)
    extensions = {
        "persistedQuery": {
            "version": 1,
            "sha256Hash": hash_value,
            "sender": "vtex.store-resources@0.x",
            "provider": "vtex.search-graphql@0.x"
        },
        "variables": encoded_vars
    }
    
    params = {
        "workspace": "master",
        "maxAge": "medium",
        "domain": "store",
        "locale": "es-MX",
        "operationName": operation_name,
        "extensions": json.dumps(extensions)
    }
    
    from urllib.parse import urlencode
    return f"{VTEX_BASE_URL}?{urlencode(params)}"


@app.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Término de búsqueda", min_length=1)
):
    """
    Busca productos y obtiene sugerencias simultáneamente (GET).
    
    Devuelve un JSON simple ideal para Agentes de IA con:
    - Sugerencias de búsqueda (autocompletado)
    - Lista de productos con imágenes y enlaces
    - Precios y detalles
    
    Ejemplo: /search?q=lego
    """
    return await execute_search(q)


@app.post("/search", response_model=SearchResponse)
async def search_post(request: SearchRequest):
    """
    Busca productos y obtiene sugerencias simultáneamente (POST).
    
    Versión POST más amigable para Agentes de IA. Acepta tanto "termino_busqueda" como "query".
    No requiere URL encoding de los espacios.
    
    Ejemplo (JSON body):
    {
      "termino_busqueda": "LEGO niño 8 años"
    }
    o
    {
      "query": "lego"
    }
    """
    # Obtener el término de búsqueda del request
    query_term = request.termino_busqueda or request.query
    
    if not query_term:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar 'termino_busqueda' o 'query' en el request body"
        )
    
    return await execute_search(query_term)


async def execute_search(query: str) -> SearchResponse:
    """Función compartida para ejecutar la búsqueda (usada por GET y POST)"""
    try:
        # Realizar ambas peticiones en paralelo
        autocomplete_vars = {"fullText": query}
        product_vars = {
            "fullText": query,
            "productOriginVtex": True,
            "simulationBehavior": "default",
            "hideUnavailableItems": False,
            "advertisementOptions": {
                "showSponsored": True,
                "sponsoredCount": 2,
                "repeatSponsoredProducts": False,
                "advertisementPlacement": "autocorrect"
            },
            "count": 12,
            "shippingOptions": [],
            "variant": None,
            "origin": "autocorrect"
        }
        
        autocomplete_url = build_url(
            "autocompleteSearchSuggestions",
            AUTOCOMPLETE_HASH,
            autocomplete_vars
        )
        
        products_url = build_url(
            "productSuggestions",
            PRODUCT_SUGGESTIONS_HASH,
            product_vars
        )
        
        # Ejecutar peticiones en paralelo
        autocomplete_response, products_response = await asyncio.gather(
            http_client.get(autocomplete_url),
            http_client.get(products_url)
        )
        
        # Procesar sugerencias
        suggestions = []
        if autocomplete_response.status_code == 200:
            autocomplete_data = autocomplete_response.json()
            suggestions = parse_suggestions(autocomplete_data)
        
        # Procesar productos
        products = []
        if products_response.status_code == 200:
            products_data = products_response.json()
            products = parse_products(products_data, query)
        
        # Procesar productos
        products = []
        if products_response.status_code == 200:
            products_data = products_response.json()
            products = parse_products(products_data, query)
        
        return SearchResponse(
            query=query,
            suggestions=suggestions,
            products=products,
            total_products=len(products)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


def parse_suggestions(data: dict) -> List[str]:
    """Extrae sugerencias de la respuesta de VTEX"""
    suggestions = []
    
    try:
        if "data" in data:
            autocomplete = data["data"].get("autocompleteSearchSuggestions", {})
            
            # Estructura actual de VTEX: searches
            if "searches" in autocomplete:
                for search in autocomplete["searches"]:
                    if "term" in search:
                        suggestions.append(search["term"])
            
            # Productos sugeridos en autocomplete
            if "productSuggestions" in autocomplete:
                for product in autocomplete["productSuggestions"]:
                    if isinstance(product, dict) and ("name" in product or "productName" in product):
                        name = product.get("name") or product.get("productName", "")
                        if name:
                            suggestions.append(name)
    except Exception as e:
        print(f"Error parsing suggestions: {e}")
    
    return list(set(suggestions))[:10]  # Máximo 10 sugerencias únicas


def parse_products(data: dict, query: str) -> List[Product]:
    """Extrae productos y los formatea para Agentes de IA"""
    products = []
    
    try:
        if "data" in data:
            result = data["data"]
            
            # Buscar la lista de productos en diferentes estructuras de VTEX
            raw_products = []
            
            # Estructura actual: productSuggestions.products
            if "productSuggestions" in result:
                suggestions_obj = result["productSuggestions"]
                if isinstance(suggestions_obj, dict) and "products" in suggestions_obj:
                    raw_products = suggestions_obj["products"]
                elif isinstance(suggestions_obj, list):
                    raw_products = suggestions_obj
            
            # Otra estructura posible: searchResult
            elif "searchResult" in result:
                search_result = result["searchResult"]
                if isinstance(search_result, dict) and "products" in search_result:
                    raw_products = search_result["products"]
                elif isinstance(search_result, list):
                    raw_products = search_result
            
            for raw_product in raw_products:
                if not isinstance(raw_product, dict):
                    continue
                
                # Extraer datos del producto
                product_id = raw_product.get("productId") or raw_product.get("cacheId") or raw_product.get("id", "")
                name = raw_product.get("productName") or raw_product.get("name", "")
                description = raw_product.get("description") or raw_product.get("shortDescription")
                
                # Precio - Estructura VTEX actual
                price = None
                if "priceRange" in raw_product and isinstance(raw_product["priceRange"], dict):
                    price_range = raw_product["priceRange"]
                    if "sellingPrice" in price_range:
                        selling = price_range["sellingPrice"]
                        if isinstance(selling, dict):
                            price_val = selling.get("lowPrice") or selling.get("highPrice", 0)
                            price = f"${price_val:.2f} MXN"
                        elif isinstance(selling, (int, float)):
                            price = f"${selling:.2f} MXN"
                
                if not price and "offer" in raw_product and isinstance(raw_product["offer"], dict):
                    offer = raw_product["offer"]
                    if "offerPrice" in offer:
                        offer_price = offer["offerPrice"]
                        if isinstance(offer_price, (int, float)):
                            price = f"${offer_price:.2f} MXN"
                
                # Imagen principal - Estructura VTEX actual
                image_url = None
                if "items" in raw_product and isinstance(raw_product["items"], list) and raw_product["items"]:
                    first_item = raw_product["items"][0]
                    if isinstance(first_item, dict) and "images" in first_item:
                        images = first_item["images"]
                        if isinstance(images, list) and len(images) > 0:
                            first_image = images[0]
                            if isinstance(first_image, dict):
                                image_url = first_image.get("imageUrl")
                
                # Buscar imagen en properties como fallback
                if not image_url and "properties" in raw_product:
                    for prop in raw_product["properties"]:
                        if prop.get("name") == "image_link":
                            values = prop.get("values", [])
                            if values:
                                image_url = values[0]
                                break
                
                # URL del producto - Estructura VTEX actual
                product_url = None
                # Preferir linkText para construir URL limpia
                link_text = raw_product.get("linkText")
                if link_text:
                    product_url = f"https://www.juguetron.mx/{link_text}/p"
                elif "link" in raw_product:
                    product_url = raw_product["link"]
                elif "properties" in raw_product:
                    for prop in raw_product["properties"]:
                        if prop.get("name") == "link":
                            values = prop.get("values", [])
                            if values:
                                product_url = values[0]
                                break
                
                # Marca
                brand = raw_product.get("brand")
                if not brand and "properties" in raw_product:
                    for prop in raw_product["properties"]:
                        if prop.get("name") == "brand":
                            values = prop.get("values", [])
                            if values:
                                brand = values[0]
                                break
                
                # Categorías
                category = None
                if "categories" in raw_product and isinstance(raw_product["categories"], list):
                    categories = raw_product["categories"]
                    if categories and len(categories) > 0:
                        # Usar la categoría más específica (última)
                        last_cat = categories[-1]
                        # Limpiar el formato /Categoria/Subcategoria/
                        category = last_cat.strip("/").split("/")[-1] if last_cat else None
                
                if name:  # Solo incluir productos con nombre
                    products.append(Product(
                        id=str(product_id),
                        name=name,
                        price=price,
                        image_url=image_url,
                        product_url=product_url,
                        brand=brand,
                        category=category,
                        description=description
                    ))
        
    except Exception as e:
        print(f"Error parsing products: {e}")
        import traceback
        traceback.print_exc()
    
    return products


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "jugueton-api"}


# ============================================================================
# MOCK API - Endpoints para Demostración
# ============================================================================

@app.post("/request_stock_check", response_model=StockCheckResponse)
async def request_stock_check(request: StockCheckRequest):
    """
    Mock Endpoint: Verificación de stock (Híbrido)
    
    Simula una consulta a sistema de inventario.
    Devuelve disponibilidad, ubicaciones y fecha de entrega estimada.
    """
    import random
    
    # Simular datos de stock
    stock_data = {
        "sku": request.sku,
        "quantity": random.choice([0, 1, 2, 5, 10, 15]),
        "status": "in_stock" if random.random() > 0.2 else "out_of_stock"
    }
    
    available_locations = [
        {
            "name": "Tienda Reforma",
            "address": "Av. Paseo de la Reforma 222, CDMX",
            "quantity": random.choice([0, 1, 2, 3]),
            "distance": f"{random.uniform(1, 5):.1f} km"
        },
        {
            "name": "Tienda Santa Fe",
            "address": "Av. Vasco de Quiroga 3800, CDMX", 
            "quantity": random.choice([0, 1, 2, 3]),
            "distance": f"{random.uniform(3, 10):.1f} km"
        }
    ]
    
    # Fecha de entrega estimada
    delivery_days = random.choice([1, 2, 3, 5])
    estimated_delivery = (datetime.now() + timedelta(days=delivery_days)).strftime("%Y-%m-%d")
    
    return StockCheckResponse(
        success=True,
        message=f"Stock verificado para SKU {request.sku}",
        stock=stock_data,
        available_locations=available_locations,
        estimated_delivery=estimated_delivery
    )


@app.post("/request_order_tracking", response_model=OrderTrackingResponse)
async def request_order_tracking(request: OrderTrackingRequest):
    """
    Mock Endpoint: Seguimiento de pedido (Mock Janis)
    
    Simula una consulta al sistema de logística Janis.
    Devuelve status del pedido, ubicación actual y tiempo estimado.
    """
    import random
    
    statuses = ["En Procesamiento", "Enviado", "En Tránsito", "Entregado", "Out for Delivery"]
    current_status = random.choice(statuses)
    
    items = [
        {
            "name": "LEGO City Police Station",
            "quantity": 1,
            "price": "$899.00 MXN"
        },
        {
            "name": "LEGO Harry Potter Mandrágora",
            "quantity": 1,
            "price": "$899.50 MXN"
        }
    ]
    
    # Fecha estimada de entrega
    delivery_days = random.choice([1, 2, 3])
    estimated_delivery = (datetime.now() + timedelta(days=delivery_days)).strftime("%Y-%m-%d")
    
    locations = ["Almacén CDMX", "Centro de Distribución Norte", "En ruta a destino", "Ubicación final"]
    current_location = random.choice(locations)
    
    return OrderTrackingResponse(
        order_id=request.order_id,
        status=current_status,
        estimated_delivery=estimated_delivery,
        current_location=current_location,
        last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        items=items,
        tracking_number=f"JUG{random.randint(10000000, 99999999)}"
    )


@app.post("/request_create_zendesk_ticket", response_model=CreateTicketResponse)
async def request_create_zendesk_ticket(request: CreateTicketRequest):
    """
    Mock Endpoint: Creación de ticket de soporte (Mock Zendesk)
    
    Simula la creación de un ticket en el sistema de soporte Zendesk.
    Asigna приорidad basado en el sentimiento del cliente.
    """
    import random
    
    # Determinar prioridad basada en el sentimiento
    if request.sentiment and request.sentiment.lower() in ["negativo", "negative"]:
        priority = "High"
        estimated_response = "4 horas"
    elif request.sentiment and request.sentiment.lower() in ["positivo", "positive"]:
        priority = "Low"
        estimated_response = "24 horas"
    else:
        priority = "Medium"
        estimated_response = "12 horas"
    
    # Generar ID del ticket
    ticket_id = f"ZDK-{random.randint(100000, 999999)}"
    
    return CreateTicketResponse(
        success=True,
        ticket_id=ticket_id,
        message=f"Ticket creado exitosamente para {request.email}",
        priority=priority,
        estimated_response_time=estimated_response
    )


@app.post("/request_invoice_generation", response_model=InvoiceGenerationResponse)
async def request_invoice_generation(request: InvoiceGenerationRequest):
    """
    Mock Endpoint: Generación de factura (Mock ERP)
    
    Simula la generación de una factura CFDI en el sistema ERP.
    Valida el RFC y genera un PDF de factura.
    """
    import random
    
    # Validar RFC básico
    if len(request.rfc) < 12:
        raise HTTPException(status_code=400, detail="RFC inválido")
    
    # Generar datos de la factura
    invoice_id = f"FAC-{random.randint(100000, 999999)}"
    total_amount = random.uniform(500, 3000)
    tax_amount = total_amount * 0.16  # IVA 16%
    
    return InvoiceGenerationResponse(
        success=True,
        invoice_id=invoice_id,
        pdf_url=f"https://api.juguetron.mx/invoices/{invoice_id}.pdf",
        message=f"Factura generada para orden {request.order_id}",
        total=f"${total_amount:.2f} MXN",
        tax=f"${tax_amount:.2f} MXN"
    )


@app.post("/generate_cfdi_invoice", response_model=InvoiceCFDIResponse)
async def generate_cfdi_invoice(request: InvoiceCFDIRequest):
    """
    Mock Endpoint: Generación de factura CFDI Juguetron
    
    Simula el proceso de facturación del portal de Juguetron
    (https://facturacionjuguetron.azurewebsites.net/)
    
    Flujo del proceso:
    1. Validar RFC (mínimo 12 caracteres, sin guiones)
    2. Validar número de ticket
       - Tienda física: formato Vxxxxxxxx
       - Tienda online: formato O401xxxxx ó O404xxxxx
    3. Validar total
       - Tienda física: debe tener punto para centavos (ej: 1452.50)
       - Tienda online: debe ser 0
    4. Validar método de pago
    
    Genera factura CFDI versión 4.0 simulada.
    """
    import random
    import re
    
    validation_errors = []
    
    # Validación RFC - mínimo 12 caracteres, sin guiones
    rfc_clean = request.rfc.replace("-", "").replace(" ", "").upper()
    if len(rfc_clean) < 12:
        validation_errors.append("RFC debe tener mínimo 12 caracteres sin incluir guiones")
    if not re.match(r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}$', rfc_clean):
        validation_errors.append("RFC no tiene el formato válido del SAT")
    
    # Validación número de ticket
    ticket_upper = request.ticket_number.upper()
    
    # Determinar tipo de tienda según el formato del ticket
    is_online = ticket_upper.startswith(('O401', 'O404'))
    is_physical = ticket_upper.startswith('V')
    
    if is_online and not re.match(r'^O401\d{5}$', ticket_upper) and not re.match(r'^O404\s*\d{5}$', ticket_upper):
        validation_errors.append("Para tienda online, el ticket debe tener formato O401xxxxx ó O404xxxxx")
    
    if is_physical and not re.match(r'^V\d{8}$', ticket_upper):
        validation_errors.append("Para tienda física, el ticket debe tener formato Vxxxxxxxx")
    
    if not is_online and not is_physical:
        validation_errors.append("Formato de ticket no válido. Debe ser Vxxxxxxxx (tienda física) o O401xxxxx/O404xxxxx (tienda online)")
    
    # Validación total
    if is_online and request.total != 0:
        validation_errors.append("Para tienda online, el total debe ser 0 (cero)")
    
    if is_physical:
        # Para tienda física, debe tener punto para centavos
        if '.' not in str(request.total):
            validation_errors.append("Para tienda física, el total debe contener un punto (.) para incluir centavos")
        # Validar que los centavos sean correctos
        try:
            total_str = str(request.total)
            if '.' in total_str:
                parts = total_str.split('.')
                if len(parts[1]) > 2:
                    validation_errors.append("El total solo puede tener hasta 2 decimales para centavos")
        except Exception as e:
            validation_errors.append(f"Error al validar el formato del total: {str(e)}")
    
    # Si hay errores de validación, regresarlos
    if validation_errors:
        return InvoiceCFDIResponse(
            success=False,
            message="Error de validación",
            validation_errors=validation_errors,
            invoice_id=None,
            pdf_url=None,
            invoice_details=None
        )
    
    # Simular proceso de generación de factura
    invoice_id = f"C{random.randint(100, 999)01-{datetime.now().year % 100:D2}-M{random.randint(100000, 999999)}"
    
    # Calcular valores
    total_amount = request.total if is_physical else round(random.uniform(200, 5000), 2)
    tax_amount = total_amount * 0.16  # IVA 16%
    subtotal = total_amount - tax_amount
    
    # Generar URL del portal SAT (simulada)
    sat_url = f"https://sat.gob.mx/cfdi/{invoice_id}"
    
    return InvoiceCFDIResponse(
        success=True,
        message=f"Factura CFDI generada exitosamente para RFC {rfc_clean}",
        invoice_id=invoice_id,
        pdf_url=f"https://facturacionjuguetron.azurewebsites.net/api/invoices/{invoice_id}.pdf",
        validation_errors=[],
        invoice_details={
            "invoice_id": invoice_id,
            "rfc": rfc_clean,
            "ticket_number": request.ticket_number,
            "subtotal": f"${subtotal:.2f} MXN",
            "iva_16": f"${tax_amount:.2f} MXN",
            "total": f"${total_amount:.2f} MXN",
            "payment_method": request.payment_method.value,
            "ticket_type": "Tienda Online" if is_online else "Tienda Física",
            "issuance_date": datetime.now().strftime("%Y-%m-%d"),
            "sat_verification": sat_url,
            "series": "M",
            "folio": f"{random.randint(10000, 99999)}",
            "cfdi_version": "4.0"
        }
    )


# ============================================================================


@app.on_event("shutdown")
async def shutdown():
    """Cerrar cliente HTTP al apagar"""
    await http_client.aclose()


import asyncio


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
