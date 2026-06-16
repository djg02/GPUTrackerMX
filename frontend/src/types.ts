export interface Listing {
  storename: string
  price: number
  currency: string
  link: string
  imageurl: string
  availabilitystatus: string
}

export interface Gpu {
  productid: string
  canonicalname: string
  brand: string
  manufacturer_normalized: string
  model_normalized: string
  coolervariant_normalized: string
  vramgb: string
  boostclock: number | null
  listings: Listing[]
  lowestPrice: number | null
  color: string | null
  oc: Boolean
}

export interface GpuResponse {
  page: number
  limit: number
  totalCount: number
  totalPages: number
  results: Gpu[]
}

export interface FilterOptions {
  brands: string[]
  manufacturers: string[]
  colors: string[]
  vramOptions: number[]
  models: string[]
  fans: number[]
  memoryTypes: string[]
  ocOptions: boolean[]
  buswidths: number[]
  interfaceVersions: string[]
}

export interface ActiveFilters {
  brand: string
  manufacturer: string
  model: string
  vram: string
  memorytype: string
  color: string
  oc: string
  inStock: boolean
  fans: string
  buswidth: string
  interfaceversion: string
}