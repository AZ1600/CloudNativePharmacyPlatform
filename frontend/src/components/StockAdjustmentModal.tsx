import { useState, type FormEvent } from 'react'
import { X } from 'lucide-react'
import type {
  AdjustmentType,
  InventoryItem,
  StockAdjustmentInput,
} from '../types/inventory'

interface StockAdjustmentModalProps {
  medicine: InventoryItem
  isSubmitting: boolean
  error?: string
  onClose: () => void
  onSubmit: (adjustment: StockAdjustmentInput) => Promise<void> | void
}

const adjustmentLabels: Record<AdjustmentType, string> = {
  RECEIPT: 'Receive stock',
  DISPENSE: 'Dispense stock',
  CORRECTION: 'Correct stock count',
  QUARANTINE: 'Quarantine stock',
}

export function StockAdjustmentModal({
  medicine,
  isSubmitting,
  error,
  onClose,
  onSubmit,
}: StockAdjustmentModalProps) {
  const [adjustmentType, setAdjustmentType] =
    useState<AdjustmentType>('RECEIPT')
  const [quantity, setQuantity] = useState(1)
  const [reason, setReason] = useState('')
  const [validationError, setValidationError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setValidationError('')

    if (!Number.isInteger(quantity)) {
      setValidationError('Quantity must be a whole number.')
      return
    }
    if (adjustmentType === 'CORRECTION' && quantity === 0) {
      setValidationError('Correction quantity cannot be zero.')
      return
    }
    if (adjustmentType !== 'CORRECTION' && quantity <= 0) {
      setValidationError('Quantity must be greater than zero.')
      return
    }
    if (!reason.trim()) {
      setValidationError('Enter a reason for this stock adjustment.')
      return
    }

    await onSubmit({
      adjustment_type: adjustmentType,
      quantity,
      reason: reason.trim(),
    })
  }

  return (
    <div className="modal-backdrop" onMouseDown={() => !isSubmitting && onClose()}>
      <section
        aria-labelledby="stock-adjustment-title"
        aria-modal="true"
        className="medicine-modal"
        role="dialog"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-header">
          <div>
            <p className="modal-eyebrow">Controlled inventory operation</p>
            <h2 id="stock-adjustment-title">Adjust stock</h2>
            <p>{medicine.drugName} · {medicine.batchNumber}</p>
          </div>
          <button
            aria-label="Close stock adjustment form"
            className="modal-close-button"
            disabled={isSubmitting}
            type="button"
            onClick={onClose}
          >
            <X aria-hidden="true" size={22} />
          </button>
        </header>

        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="current-stock-summary">
            <span>Current available stock</span>
            <strong>{medicine.quantity} units</strong>
          </div>

          <div className="form-grid">
            <label className="form-field form-field-wide">
              <span>Operation</span>
              <select
                value={adjustmentType}
                onChange={(event) => {
                  setAdjustmentType(event.target.value as AdjustmentType)
                  setQuantity(1)
                }}
              >
                {Object.entries(adjustmentLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </label>

            <label className="form-field form-field-wide">
              <span>
                {adjustmentType === 'CORRECTION'
                  ? 'Quantity difference (+ or −)'
                  : 'Quantity'}
              </span>
              <input
                required
                step="1"
                type="number"
                value={quantity}
                onChange={(event) => setQuantity(Number(event.target.value))}
              />
              {adjustmentType === 'CORRECTION' && (
                <small>Use a positive value to add stock or a negative value to remove it.</small>
              )}
            </label>

            <label className="form-field form-field-wide">
              <span>Reason</span>
              <textarea
                maxLength={500}
                required
                rows={3}
                value={reason}
                placeholder="For example, delivery note DN-1042 received and checked"
                onChange={(event) => setReason(event.target.value)}
              />
            </label>
          </div>

          {(validationError || error) && (
            <div className="modal-error" role="alert">
              {validationError || error}
            </div>
          )}

          <footer className="modal-actions">
            <button className="secondary-button" disabled={isSubmitting} type="button" onClick={onClose}>
              Cancel
            </button>
            <button className="primary-button" disabled={isSubmitting} type="submit">
              {isSubmitting ? 'Saving adjustment…' : adjustmentLabels[adjustmentType]}
            </button>
          </footer>
        </form>
      </section>
    </div>
  )
}
