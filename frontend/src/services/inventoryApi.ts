import type {
  AdjustmentType,
  AuditEntry,
  InventoryItem,
  StockAdjustmentInput,
} from '../types/inventory'

interface ApiInventoryItem {
  id: string
  drug_name: string
  batch_number?: string
  category?: string
  quantity: number
  reorder_level: number
  expiry_date?: string
  supplier?: string
  location?: string
}

interface InventoryResponse {
  items: ApiInventoryItem[]
  count: number
}

export interface InventoryApiResult {
  items: InventoryItem[]
  source: 'api' | 'mock'
  message?: string
}

const apiUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '')

function mapInventoryItem(item: ApiInventoryItem): InventoryItem {
  return {
    id: item.id,
    drugName: item.drug_name,
    batchNumber: item.batch_number ?? 'Not provided',
    category: item.category ?? 'Uncategorised',
    quantity: item.quantity,
    reorderLevel: item.reorder_level,
    expiryDate: item.expiry_date ?? '',
    supplier: item.supplier ?? 'Not provided',
    location: item.location ?? 'Not assigned',
  }
}

export async function fetchInventory(
  fallbackItems: InventoryItem[],
): Promise<InventoryApiResult> {
  if (!apiUrl) {
    return {
      items: fallbackItems,
      source: 'mock',
      message: 'VITE_API_URL is not configured.',
    }
  }

  const token = window.localStorage.getItem('pharmaflow_access_token')

  if (!token) {
    return {
      items: fallbackItems,
      source: 'mock',
      message: 'No authentication token is available.',
    }
  }

  try {
    const response = await fetch(`${apiUrl}/drugs`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error(`Inventory API returned HTTP ${response.status}`)
    }

    const data = (await response.json()) as InventoryResponse

    if (!Array.isArray(data.items)) {
      throw new Error('Inventory API returned an invalid response.')
    }

    return {
      items: data.items.map(mapInventoryItem),
      source: 'api',
    }
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Unable to load inventory.'

    console.error('Inventory API request failed:', error)

    return {
      items: fallbackItems,
      source: 'mock',
      message,
    }
  }
}

export interface CreateMedicineInput {
  drug_name: string
  batch_number: string
  quantity: number
  reorder_level: number
  expiry_date: string
  supplier?: string
}

interface CreateMedicineResponse {
  message: string
  drug_id: string
  tenant_id: string
}

export async function createMedicine(
  medicine: CreateMedicineInput,
): Promise<CreateMedicineResponse> {
  if (!apiUrl) {
    throw new Error(
      'The API URL is not configured. Add VITE_API_URL to frontend/.env.',
    )
  }

  const token = window.localStorage.getItem('pharmaflow_access_token')

  if (!token) {
    throw new Error(
      'Authentication is required. No pharmaflow_access_token was found.',
    )
  }

  const response = await fetch(`${apiUrl}/drugs`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(medicine),
  })

  let data: CreateMedicineResponse | { message?: string }

  try {
    data = (await response.json()) as
      | CreateMedicineResponse
      | { message?: string }
  } catch {
    throw new Error(`Medicine API returned HTTP ${response.status}`)
  }

  if (!response.ok) {
    throw new Error(
      data.message ?? `Medicine API returned HTTP ${response.status}`,
    )
  }

  return data as CreateMedicineResponse
}

interface StockAdjustmentResponse {
  message: string
  adjustment_id: string
  drug_id: string
  previous_quantity: number
  new_quantity: number
  quantity_change: number
  adjustment_type: AdjustmentType
  created_at: string
}

interface ApiAuditEntry {
  id: string
  drug_id: string
  drug_name: string
  batch_number: string
  adjustment_type: AdjustmentType
  quantity_change: number
  previous_quantity: number
  new_quantity: number
  reason: string
  created_at: string
  created_by: string
}

interface AuditResponse {
  items: ApiAuditEntry[]
  count: number
}

function requireApiConfiguration() {
  if (!apiUrl) {
    throw new Error(
      'The API URL is not configured. Add VITE_API_URL to frontend/.env.',
    )
  }

  const token = window.localStorage.getItem('pharmaflow_access_token')
  if (!token) {
    throw new Error('Authentication is required. Sign in before continuing.')
  }

  return { apiUrl, token }
}

async function parseApiResponse<T extends object>(response: Response): Promise<T> {
  let data: T | { message?: string }
  try {
    data = (await response.json()) as T | { message?: string }
  } catch {
    throw new Error(`Pharmacy API returned HTTP ${response.status}`)
  }

  if (!response.ok) {
    throw new Error(
      ('message' in data && data.message) ||
        `Pharmacy API returned HTTP ${response.status}`,
    )
  }
  return data as T
}

export async function adjustStock(
  drugId: string,
  adjustment: StockAdjustmentInput,
): Promise<StockAdjustmentResponse> {
  const configuration = requireApiConfiguration()
  const response = await fetch(
    `${configuration.apiUrl}/drugs/${encodeURIComponent(drugId)}/adjustments`,
    {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${configuration.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(adjustment),
    },
  )
  return parseApiResponse<StockAdjustmentResponse>(response)
}

export async function fetchAuditLog(): Promise<AuditEntry[]> {
  const configuration = requireApiConfiguration()
  const response = await fetch(`${configuration.apiUrl}/audit`, {
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${configuration.token}`,
    },
  })
  const data = await parseApiResponse<AuditResponse>(response)
  return data.items.map((item) => ({
    id: item.id,
    drugId: item.drug_id,
    drugName: item.drug_name,
    batchNumber: item.batch_number,
    adjustmentType: item.adjustment_type,
    quantityChange: item.quantity_change,
    previousQuantity: item.previous_quantity,
    newQuantity: item.new_quantity,
    reason: item.reason,
    createdAt: item.created_at,
    createdBy: item.created_by,
  }))
}
