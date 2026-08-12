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

export type AdjustmentType =
  | 'RECEIPT'
  | 'DISPENSE'
  | 'CORRECTION'
  | 'QUARANTINE'

export interface StockAdjustmentInput {
  adjustment_type: AdjustmentType
  quantity: number
  reason: string
}

export interface AuditEntry {
  id: string
  drugId: string
  drugName: string
  batchNumber: string
  adjustmentType: AdjustmentType
  quantityChange: number
  previousQuantity: number
  newQuantity: number
  reason: string
  createdAt: string
  createdBy: string
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
