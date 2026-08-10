import type { InventoryItem } from '../types/inventory'

interface ApiInventoryItem {
  drug_id: string
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
    id: item.drug_id,
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