"""
Juguetron API Proxy
API simple para búsqueda y sugerencias de productos de Juguetron.mx
Diseñado para Agentes de IA
"""

import base64
import json
import httpx
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Juguetron API",
    description="API simple para búsqueda de productos en Juguetron.mx",
    version="1.0.0"
)

# Configurar CORS para agentes de IA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    Busca productos y obtiene sugerencias simultáneamente.
    
    Devuelve un JSON simple ideal para Agentes de IA con:
    - Sugerencias de búsqueda (autocompletado)
    - Lista de productos con imágenes y enlaces
    - Precios y detalles
    
    Ejemplo: /search?q=lego
    """
    try:
        # Realizar ambas peticiones en paralelo
        autocomplete_vars = {"fullText": q}
        product_vars = {
            "fullText": q,
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
            products = parse_products(products_data, q)
        
        return SearchResponse(
            query=q,
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
    return {"status": "healthy", "service": "juguetron-api"}


@app.on_event("shutdown")
async def shutdown():
    """Cerrar cliente HTTP al apagar"""
    await http_client.aclose()


import asyncio


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
