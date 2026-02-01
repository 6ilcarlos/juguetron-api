# Juguetron API Proxy

API simple para búsqueda y sugerencias de productos de Juguetron.mx, diseñado para Agentes de IA.

## Uso en Replit

1. Copia `app.py` y `requirements.txt` a tu proyecto Replit
2. Replit instalará las dependencias automáticamente
3. El servidor se iniciará en el puerto 8000

## Endpoints

### `GET /search?q=termino`

Busca productos y devuelve sugerencias (GET con query params).

**Ejemplos:**
```
GET /search?q=lego
GET /search?q=barbie
GET /search?q=carros
```

**Nota:** Los espacios en la URL deben estar URL-encoded (ejemplo: `%20` en lugar de espacio)

---

### `POST /search` (Recomendado para Agentes de IA)

Busca productos y devuelve sugerencias usando JSON body. **Más amigable para Agentes de IA** porque no requiere URL encoding.

**Request (JSON body):**
```json
{
  "termino_busqueda": "LEGO niño 8 años"
}
```
o alternativamente:
```json
{
  "query": "lego"
}
```

**Respuesta:** Igual que el endpoint GET

**Ventajas del endpoint POST:**
- No requiere URL encoding de espacios y caracteres especiales
- Acepta nombres de campos más descriptivos (`termino_busqueda`)
- Más natural para integraciones con Agentes de IA

--

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

---

## Endpoints Mock para Demostración

Estos endpoints simulan integraciones con sistemas externos para demostración:

### `POST /request_stock_check`

Mock endpoint para verificación de stock (Híbrido).

**Request:**
```json
{
  "sku": "12345",
  "zip_code": "02300"
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Stock verificado para SKU 12345",
  "stock": {
    "sku": "12345",
    "quantity": 5,
    "status": "in_stock"
  },
  "available_locations": [
    {
      "name": "Tienda Reforma",
      "address": "Av. Paseo de la Reforma 222, CDMX",
      "quantity": 2,
      "distance": "2.3 km"
    }
  ],
  "estimated_delivery": "2025-02-03"
}
```

### `POST /request_order_tracking`

Mock endpoint para seguimiento de pedido (Mock Janis).

**Request:**
```json
{
  "order_id": "ORD-998877"
}
```

**Respuesta:**
```json
{
  "order_id": "ORD-998877",
  "status": "En Tránsito",
  "estimated_delivery": "2025-02-04",
  "current_location": "Centro de Distribución Norte",
  "last_update": "2025-02-01 10:30:00",
  "items": [
    {
      "name": "LEGO City Police Station",
      "quantity": 1,
      "price": "$899.00 MXN"
    }
  ],
  "tracking_number": "JUG45678901"
}
```

### `POST /request_create_zendesk_ticket`

Mock endpoint para crear ticket de soporte (Mock Zendesk).

**Request:**
```json
{
  "email": "cliente@email.com",
  "category": "Producto Dañado",
  "description": "La caja llegó abierta",
  "sentiment": "Negativo"
}
```

**Respuesta:**
```json
{
  "success": true,
  "ticket_id": "ZDK-567890",
  "message": "Ticket creado exitosamente para cliente@email.com",
  "priority": "High",
  "estimated_response_time": "4 horas"
}
```

**Categorías disponibles:**
- `Producto Dañado`
- `Reembolso`
- `Cambio`
- `General`

### `POST /request_invoice_generation`

Mock endpoint para generación de factura (Mock ERP).

**Request:**
```json
{
  "order_id": "ORD-123",
  "rfc": "XAXX010101000"
}
```

**Respuesta:**
```json
{
  "success": true,
  "invoice_id": "FAC-789012",
  "pdf_url": "https://api.juguetron.mx/invoices/FAC-789012.pdf",
  "message": "Factura generada para orden ORD-123",
  "total": "$1150.00 MXN",
  "tax": "$150.00 MXN"
}
```

### `POST /generate_cfdi_invoice` (Nuevo - Simula el Portal de Facturación Juguetron)

Mock endpoint para facturación CFDI de Juguetron, basado en ingeniería inversa de https://facturacionjuguetron.azurewebsites.net/

**Request:**
```json
{
  "rfc": "XAXX010101000",
  "ticket_number": "V12345678",
  "total": 1452.50,
  "payment_method": "Efectivo"
}
```

**Parámetros:**
- `rfc`: RFC del cliente (mínimo 12 caracteres, sin guiones, formato SAT)
- `ticket_number`: Número de ticket
  - Tienda física: formato `Vxxxxxxxx`
  - Tienda online: formato `O401xxxxx` ó `O404xxxxx`
- `total`: Total de la compra
  - Tienda física: debe tener punto para centavos (ej: `1452.50`)
  - Tienda online: debe ser `0`
- `payment_method`: Método de pago
  - `Efectivo`
  - `Tarjeta de Débito`
  - `Tarjeta de Crédito`
  - `Transferencia electrónica de fondos`

**Respuesta (Éxito):**
```json
{
  "success": true,
  "message": "Factura CFDI generada exitosamente para RFC XAXX010101000",
  "invoice_id": "C10126-M24-543210",
  "pdf_url": "https://facturacionjuguetron.azurewebsites.net/api/invoices/C10126-M24-543210.pdf",
  "validation_errors": [],
  "invoice_details": {
    "invoice_id": "C10126-M24-543210",
    "rfc": "XAXX010101000",
    "ticket_number": "V12345678",
    "subtotal": "$1249.57 MXN",
    "iva_16": "$202.93 MXN",
    "total": "$1452.50 MXN",
    "payment_method": "Efectivo",
    "ticket_type": "Tienda Física",
    "issuance_date": "2026-02-01",
    "sat_verification": "https://sat.gob.mx/cfdi/C10126-M24-543210",
    "series": "M",
    "folio": "54321",
    "cfdi_version": "4.0"
  }
}
```

**Respuesta (Error de validación):**
```json
{
  "success": false,
  "message": "Error de validación",
  "validation_errors": [
    "RFC debe tener mínimo 12 caracteres sin incluir guiones",
    "Formato de ticket no válido"
  ],
  "invoice_id": null,
  "pdf_url": null,
  "invoice_details": null
}
```

--

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
        # Usando POST (recomendado para Agentes de IA)
        response = await client.post(
            "https://tu-api.replit.app/search",
            json={"termino_busqueda": query}
        )
        data = response.json()
        
        # O alternativamente usando GET:
        # import urllib.parse
        # encoded_query = urllib.parse.quote(query)
        # response = await client.get(
        #     f"https://tu-api.replit.app/search?q={encoded_query}"
        # )
        
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
  // Usando POST (recomendado para Agentes de IA)
  const response = await fetch(
    "https://tu-api.replit.app/search",
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ termino_busqueda: query })
    }
  );
  const data = await response.json();
  
  // O alternativamente usando GET:
  // const response = await fetch(
  //   `https://tu-api.replit.app/search?q=${encodeURIComponent(query)}`
  // );
  
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
