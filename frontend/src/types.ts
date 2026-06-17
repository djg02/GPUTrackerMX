export interface Listing {
  storename: string
  price: number
  currency: string
  link: string
  imageurl: string
  availabilitystatus: string
  lastseen: string
  currentpriceupdated: string
}

export interface Gpu {
  productid: string
  producttype: string
  canonicalname: string
  brand: string
  series: string
  manufacturer_normalized: string
  model_normalized: string
  coolervariant_normalized: string
  vramgb: string
  memorytype: string
  buswidth: number
  interfaceversion: string
  color: string | null
  fans: number
  boostclock: number | null
  baseclock: number | null
  listings: Listing[]
  lowestPrice: number | null
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
  brand: string[]
  manufacturer: string[]
  model: string[]
  vram: string[]
  memorytype: string[]
  color: string[]
  oc: string
  inStock: boolean
  fans: string[]
  buswidth: string[]
  interfaceversion: string[]
}