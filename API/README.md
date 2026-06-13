# GPU Tracker API

A REST API for tracking and comparing GPU prices across Mexican retailers.

## Stack

* Node.js + Express + TypeScript
* PostgreSQL (via `pg`)

## Endpoints

### `GET /api/gpus`

Returns a paginated, filterable, sortable list of GPU products with their listings across stores.

**Query Parameters**

|Param|Type|Description|
|-|-|-|
|`page`|integer|Page number (default `1`, min `1`)|
|`limit`|integer|Results per page (default `20`, range `1`-`50`)|
|`sort`|string|`price_asc`, `price_desc`, `name_asc`, `name_desc` (default: by `productid`)|
|`search`|string|Free-text search against `canonicalname`. Multi-word search ANDs each word.|
|`brand`|string|Exact match on `brand` (e.g. `NVIDIA`)|
|`manufacturer`|string|Exact match on `manufacturer_normalized` (e.g. `ZOTAC`)|
|`model`|string|Exact match on `model_normalized`|
|`color`|string|Exact match on `color`|
|`memorytype`|string|Exact match on `memorytype` (e.g. `GDDR7`)|
|`interfaceversion`|string|Exact match on `interfaceversion` (e.g. `5.0`)|
|`minVram`|number|Minimum VRAM in GB (`vramgb >=`)|
|`buswidth`|number|Exact match on `buswidth`|
|`fans`|number|Exact match on `fans`|
|`oc`|boolean|`true`/`false` — filters on `oc`|
|`minPrice`|number|Minimum price (≥ 0), based on lowest **in-stock** listing|
|`maxPrice`|number|Maximum price (≥ 0), based on lowest **in-stock** listing|
|`inStock`|boolean|`true` — only products with at least one in-stock listing|

**Notes**

* `minPrice`/`maxPrice` only consider listings with `availabilitystatus` of `InStock` or `Available`. Products with no in-stock listings are excluded when these filters are applied.
* Invalid `page`, `limit`, `minPrice`, or `maxPrice` return `400 Bad Request`.

**Response**

```json
{
  "page": 1,
  "limit": 20,
  "totalCount": 287,
  "totalPages": 15,
  "results": [
    {
      "productid": "4797",
      "canonicalname": "ZOTAC NVIDIA GeForce RTX 5080 Solid OC 16.0GB GDDR7 White",
      "brand": "NVIDIA",
      "manufacturer_normalized": "ZOTAC",
      "model_normalized": "GeForce RTX 5080",
      "coolervariant_normalized": "Solid",
      "vramgb": "16.0",
      "listings": [
        {
          "storename": "Cyberpuerta",
          "price": 26449,
          "currency": "MXN",
          "link": "...",
          "imageurl": "...",
          "availabilitystatus": "InStock"
        }
      ],
      "lowestPrice": 26449
    }
  ]
}
```

### `GET /api/gpus/filters`

Returns distinct values for each filterable field, for building filter UI (dropdowns, checkboxes).

**Response**

```json
{
  "brands": ["AMD", "NVIDIA"],
  "manufacturers": ["ASUS", "MSI", "ZOTAC", "..."],
  "colors": ["White", "..."],
  "vramOptions": [8, 12, 16, 24, 32],
  "models": ["GeForce RTX 5080", "..."],
  "fans": [2, 3],
  "memoryTypes": ["GDDR6", "GDDR7"],
  "ocOptions": [true, false],
  "buswidths": [192, 256, 384],
  "interfaceVersions": ["4.0", "5.0"]
}
```

### `GET /api/gpus/:id`

Returns full details for a single product, including all listings across stores.

**Response**

```json
{
  "productid": "4797",
  "producttype": "GPU",
  "canonicalname": "ZOTAC NVIDIA GeForce RTX 5080 Solid OC 16.0GB GDDR7 White",
  "brand": "NVIDIA",
  "series": "GeForce RTX 50",
  "manufacturer_normalized": "ZOTAC",
  "model_normalized": "GeForce RTX 5080",
  "coolervariant_normalized": "Solid",
  "vramgb": "16.0",
  "memorytype": "GDDR7",
  "buswidth": 256,
  "interfaceversion": "5.0",
  "color": "White",
  "fans": 3,
  "boostclock": null,
  "baseclock": null,
  "listings": [same shape as above],
  "lowestPrice": 26449
}
```

**Errors**

* `404 Not Found` — `{ "error": "Product not found" }` if no product matches `:id`.

## Known Limitations / TODOs

* `canonicalname` stores VRAM as `"16.0GB"` (from `build_canonical_name`); a future cleanup could strip `.0` at the source (requires a data migration for existing rows).
* Non-price numeric filters (`minVram`, `buswidth`, `fans`) silently return 0 results if given a non-numeric value, rather than `400`. Acceptable since the frontend is expected to populate these from `/api/gpus/filters` (dropdowns), not free text.

