# Juguetron API Proxy

API simple para búsqueda y sugerencias de productos de Juguetron.mx, diseñado para Agentes de IA.

## Uso en Replit

1. Copia `app.py` y `requirements.txt` a tu proyecto Replit
2. Replit instalará las dependencias automáticamente
3. El servidor se iniciará en el puerto 8000

## Endpoints

### `GET /search?q=termino`

Busca productos y devuelve sugerencias en una sola respuesta.

**Ejemplos:**
```
GET /search?q=lego
GET /search?q=barbie
GET /search?q=carros
```

**Respuesta:**
```json
{
  "query": "lego",
  "suggestions": [
    "lego",
    "lego cars",
    "lego marvel",
    "lego star wars",
    "lego minecraft"
  ],
  "products": [
    {
      "id": "3713",
      "name": "Juguete Pre Escolar Cocina de Mini Chef con Accesorios",
      "description": "Despierta el amor por la cocina con la Cocina de Mini Chef...",
      "price": "$799.20 MXN",
      "image_url": "https://juguetron.vtexassets.com/arquivos/ids/187178/...",
      "product_url": "https://www.juguetron.mx/juguete-pre-escolar-cocina-de-mini-chef-con-accesorios/p",
      "brand": "Importacion Juguetron",
      "category": "Creatividad y Arte"
    },
    {
      "id": "184889",
      "name": "LEGO Harry Potter Mandrágora 76433",
      "description": null,
      "price": "$899.50 MXN",
      "image_url": "https://juguetron.vtexassets.com/arquivos/ids/185330/...",
      "product_url": "https://www.juguetron.mx/lego-harry-potter-mandragora-76433/p",
      "brand": "LEGO",
      "category": "Harry Potter"
    }
  ],
  "total_products": 2
}
```

### `GET /health`

Verifica que el API esté funcionando.

## Estructura de la respuesta

- `query`: Término de búsqueda original
- `suggestions`: Lista de sugerencias de búsqueda (autocompletado)
- `products`: Lista de productos encontrados con:
  - `id`: ID del producto
  - `name`: Nombre del producto
  - `description`: Descripción corta
  - `price`: Precio en formato MXN
  - `image_url`: URL de la imagen del producto
  - `product_url`: URL directa a la página del producto
  - `brand`: Marca del producto
  - `category`: Categoría del producto
- `total_products`: Cantidad de productos devueltos (máximo 12)

## Ejemplo de uso con curl

```bash
curl "http://localhost:8000/search?q=lego"
```

## Uso con Agentes de IA

Este API está diseñado para ser consumido fácilmente por Agentes de IA. La estructura de respuesta incluye todo lo necesario para interactuar con clientes:

- **Sugerencias**: Ayudan a completar las búsquedas de los clientes
- **Productos**: Incluyen precios, imágenes y enlaces directos
- **Enlaces**: URLs directas a la página del producto y a las imágenes

### Ejemplo de integración (Python)

```python
import httpx

async def get_product_suggestions(query: str):
    """Obtiene sugerencias de productos para un Agente de IA"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://tu-api.replit.app/search?q={query}"
        )
        data = response.json()
        
        # Crear mensaje para el cliente
        message = f"Encontré {data['total_products']} productos de {query}:\n\n"
        
        for product in data['products']:
            message += f"• {product['name']}\n"
            message += f"  Precio: {product['price']}\n"
            message += f"  Ver detalles: {product['product_url']}\n\n"
        
        # Usar sugerencias si no hay suficientes productos
        if data['total_products'] < 3 and data['suggestions']:
            message += f"¿Quizás querías buscar: {', '.join(data['suggestions'][:3])}?"
        
        return message
```

### Ejemplo de integración (JavaScript/Node)

```javascript
async function getProductSuggestions(query) {
  const response = await fetch(
    `https://tu-api.replit.app/search?q=${query}`
  );
  const data = await response.json();
  
  // Crear mensaje para el cliente
  let message = `Encontré ${data.total_products} productos de ${query}:\n\n`;
  
  data.products.forEach(product => {
    message += `• ${product.name}\n`;
    message += `  Precio: ${product.price}\n`;
    message += `  Imagen: ${product.image_url}\n`;
    message += `  Ver detalles: ${product.product_url}\n\n`;
  });
  
  return message;
}
```
