export type StockStatus = 'Healthy' | 'Low stock' | 'Out of stock'

export interface InventoryItem {
  id: string
  drugName: string
  batchNumber: string
  category: string
  quantity: number
  reorderLevel: number
  expiryDate: string
  supplier: string
  location: string
}

export function getStockStatus(item: InventoryItem): StockStatus {
  if (item.quantity === 0) {
    return 'Out of stock'
  }

  if (item.quantity <= item.reorderLevel) {
    return 'Low stock'
  }

  return 'Healthy'
}