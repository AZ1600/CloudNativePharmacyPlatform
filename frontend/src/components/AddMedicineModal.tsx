import {
  useEffect,
  useState,
  type FormEvent,
} from 'react'
import { X } from 'lucide-react'
import type { CreateMedicineInput } from '../services/inventoryApi'

interface AddMedicineModalProps {
  isOpen: boolean
  isSubmitting: boolean
  error?: string
  onClose: () => void
  onSubmit: (medicine: CreateMedicineInput) => Promise<void> | void
}

const initialForm: CreateMedicineInput = {
  drug_name: '',
  batch_number: '',
  quantity: 0,
  reorder_level: 0,
  expiry_date: '',
  supplier: '',
}

export function AddMedicineModal({
  isOpen,
  isSubmitting,
  error,
  onClose,
  onSubmit,
}: AddMedicineModalProps) {
  const [form, setForm] =
    useState<CreateMedicineInput>(initialForm)

  const [validationError, setValidationError] = useState('')

  useEffect(() => {
    if (!isOpen) {
      return
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape' && !isSubmitting) {
        onClose()
      }
    }

    window.addEventListener('keydown', handleEscape)

    return () => {
      window.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, isSubmitting, onClose])

  if (!isOpen) {
    return null
  }

  function updateField<K extends keyof CreateMedicineInput>(
    field: K,
    value: CreateMedicineInput[K],
  ) {
    setForm((currentForm) => ({
      ...currentForm,
      [field]: value,
    }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setValidationError('')

    if (!form.drug_name.trim()) {
      setValidationError('Enter the medicine name.')
      return
    }

    if (!form.batch_number.trim()) {
      setValidationError('Enter the batch number.')
      return
    }

    if (form.quantity < 0) {
      setValidationError('Quantity cannot be negative.')
      return
    }

    if (form.reorder_level < 0) {
      setValidationError('Reorder level cannot be negative.')
      return
    }

    if (!form.expiry_date) {
      setValidationError('Select an expiry date.')
      return
    }

    await onSubmit({
      ...form,
      drug_name: form.drug_name.trim(),
      batch_number: form.batch_number.trim(),
      supplier: form.supplier?.trim() || undefined,
    })
  }

  function handleBackdropClick() {
    if (!isSubmitting) {
      onClose()
    }
  }

  function handleClose() {
    setForm(initialForm)
    setValidationError('')
    onClose()
  }

  return (
    <div
      className="modal-backdrop"
      onMouseDown={handleBackdropClick}
    >
      <section
        aria-labelledby="add-medicine-title"
        aria-modal="true"
        className="medicine-modal"
        role="dialog"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-header">
          <div>
            <p className="modal-eyebrow">Inventory management</p>

            <h2 id="add-medicine-title">
              Add medicine
            </h2>

            <p>
              Add a new batch to the pharmacy inventory.
            </p>
          </div>

          <button
            aria-label="Close add medicine form"
            className="modal-close-button"
            disabled={isSubmitting}
            type="button"
            onClick={handleClose}
          >
            <X aria-hidden="true" size={22} />
          </button>
        </header>

        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="form-field form-field-wide">
              <span>Medicine name</span>

              <input
                autoFocus
                required
                type="text"
                value={form.drug_name}
                placeholder="For example, Amoxicillin 500 mg"
                onChange={(event) =>
                  updateField('drug_name', event.target.value)
                }
              />
            </label>

            <label className="form-field">
              <span>Batch number</span>

              <input
                required
                type="text"
                value={form.batch_number}
                placeholder="AMX-2408-17"
                onChange={(event) =>
                  updateField('batch_number', event.target.value)
                }
              />
            </label>

            <label className="form-field">
              <span>Supplier</span>

              <input
                type="text"
                value={form.supplier ?? ''}
                placeholder="MedCore Distribution"
                onChange={(event) =>
                  updateField('supplier', event.target.value)
                }
              />
            </label>

            <label className="form-field">
              <span>Quantity</span>

              <input
                min="0"
                required
                type="number"
                value={form.quantity}
                onChange={(event) =>
                  updateField(
                    'quantity',
                    Number(event.target.value),
                  )
                }
              />
            </label>

            <label className="form-field">
              <span>Reorder level</span>

              <input
                min="0"
                required
                type="number"
                value={form.reorder_level}
                onChange={(event) =>
                  updateField(
                    'reorder_level',
                    Number(event.target.value),
                  )
                }
              />
            </label>

            <label className="form-field form-field-wide">
              <span>Expiry date</span>

              <input
                required
                type="date"
                value={form.expiry_date}
                onChange={(event) =>
                  updateField('expiry_date', event.target.value)
                }
              />
            </label>
          </div>

          {(validationError || error) && (
            <div className="modal-error" role="alert">
              {validationError || error}
            </div>
          )}

          <footer className="modal-actions">
            <button
              className="secondary-button"
              disabled={isSubmitting}
              type="button"
              onClick={handleClose}
            >
              Cancel
            </button>

            <button
              className="primary-button"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? 'Adding medicine…' : 'Add medicine'}
            </button>
          </footer>
        </form>
      </section>
    </div>
  )
}
