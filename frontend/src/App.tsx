import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  Bell,
  Boxes,
  ChevronDown,
  CirclePlus,
  ClipboardList,
  LayoutDashboard,
  Menu,
  PackageCheck,
  Search,
  Settings,
  ShieldCheck,
  Stethoscope,
  UserRound,
  XCircle,
} from 'lucide-react'
import './App.css'
import { AddMedicineModal } from './components/AddMedicineModal'
import { StockAdjustmentModal } from './components/StockAdjustmentModal'
import { mockInventory } from './data/mockInventory'
import {
  createMedicine,
  adjustStock,
  fetchAuditLog,
  fetchInventory,
  type CreateMedicineInput,
} from './services/inventoryApi'
import {
  getStockStatus,
  type AuditEntry,
  type InventoryItem,
  type StockAdjustmentInput,
  type StockStatus,
} from './types/inventory'

type FilterValue = 'All' | StockStatus

function App() {
  const [inventory, setInventory] =
    useState<InventoryItem[]>(mockInventory)
  const [dataSource, setDataSource] = useState<'api' | 'mock'>('mock')
  const [dataMessage, setDataMessage] = useState(
    'Using local demonstration data',
  )
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<FilterValue>('All')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [addMedicineOpen, setAddMedicineOpen] = useState(false)
  const [submittingMedicine, setSubmittingMedicine] = useState(false)
  const [medicineError, setMedicineError] = useState('')
  const [medicineSuccess, setMedicineSuccess] = useState('')
  const [selectedMedicine, setSelectedMedicine] =
    useState<InventoryItem | null>(null)
  const [submittingAdjustment, setSubmittingAdjustment] = useState(false)
  const [adjustmentError, setAdjustmentError] = useState('')
  const [auditHistory, setAuditHistory] = useState<AuditEntry[]>([])

  useEffect(() => {
    let active = true

    async function loadInventory() {
      const result = await fetchInventory(mockInventory)

      if (!active) {
        return
      }

      setInventory(result.items)
      setDataSource(result.source)
      setDataMessage(
        result.source === 'api'
          ? 'Inventory loaded from the pharmacy API'
          : result.message ?? 'Using local demonstration data',
      )

      if (result.source === 'api') {
        try {
          setAuditHistory(await fetchAuditLog())
        } catch (error) {
          console.error('Audit API request failed:', error)
        }
      }
    }

    void loadInventory()

    return () => {
      active = false
    }
  }, [])

  async function handleAddMedicine(medicine: CreateMedicineInput) {
    setSubmittingMedicine(true)
    setMedicineError('')
    setMedicineSuccess('')

    try {
      await createMedicine(medicine)
      setAddMedicineOpen(false)
      setMedicineSuccess(`${medicine.drug_name} was added successfully.`)

      const refreshedInventory = await fetchInventory([])

      if (refreshedInventory.source === 'api') {
        setInventory(refreshedInventory.items)
        setDataSource('api')
        setDataMessage('Inventory loaded from the pharmacy API')
      } else {
        setDataMessage(
          refreshedInventory.message ??
            'Medicine was saved, but inventory could not be refreshed.',
        )
        setMedicineSuccess(
          `${medicine.drug_name} was added, but the inventory could not be refreshed. Reload the page to try again.`,
        )
      }
    } catch (error) {
      setMedicineError(
        error instanceof Error ? error.message : 'Unable to add medicine.',
      )
    } finally {
      setSubmittingMedicine(false)
    }
  }

  async function handleStockAdjustment(adjustment: StockAdjustmentInput) {
    if (!selectedMedicine) {
      return
    }

    setSubmittingAdjustment(true)
    setAdjustmentError('')
    setMedicineSuccess('')

    try {
      const result = await adjustStock(selectedMedicine.id, adjustment)
      setInventory((currentInventory) =>
        currentInventory.map((item) =>
          item.id === selectedMedicine.id
            ? { ...item, quantity: result.new_quantity }
            : item,
        ),
      )
      setSelectedMedicine(null)
      setMedicineSuccess(
        `${selectedMedicine.drugName} stock changed from ${result.previous_quantity} to ${result.new_quantity} units.`,
      )

      try {
        setAuditHistory(await fetchAuditLog())
      } catch (error) {
        console.error('Audit history refresh failed:', error)
      }
    } catch (error) {
      setAdjustmentError(
        error instanceof Error ? error.message : 'Unable to adjust stock.',
      )
    } finally {
      setSubmittingAdjustment(false)
    }
  }

  const filteredInventory = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()

    return inventory.filter((item) => {
      const status = getStockStatus(item)
      const matchesFilter = filter === 'All' || status === filter
      const matchesSearch =
        normalizedSearch.length === 0 ||
        item.drugName.toLowerCase().includes(normalizedSearch) ||
        item.batchNumber.toLowerCase().includes(normalizedSearch) ||
        item.supplier.toLowerCase().includes(normalizedSearch)

      return matchesFilter && matchesSearch
    })
  }, [filter, inventory, search])

  const lowStockCount = inventory.filter(
    (item) => getStockStatus(item) === 'Low stock',
  ).length

  const outOfStockCount = inventory.filter(
    (item) => getStockStatus(item) === 'Out of stock',
  ).length

  const healthyCount = inventory.filter(
    (item) => getStockStatus(item) === 'Healthy',
  ).length

  const totalUnits = inventory.reduce(
    (total, item) => total + item.quantity,
    0,
  )

  return (
    <div className="app-shell">
      <aside className={mobileNavOpen ? 'sidebar sidebar--open' : 'sidebar'}>
        <div className="brand">
          <div className="brand__mark">
            <Stethoscope size={23} aria-hidden="true" />
          </div>
          <div>
            <strong>PharmaFlow</strong>
            <span>Inventory operations</span>
          </div>
        </div>

        <nav className="navigation" aria-label="Primary navigation">
          <p className="navigation__label">Workspace</p>

          <a
            className="navigation__item navigation__item--active"
            href="#dashboard"
          >
            <LayoutDashboard size={19} aria-hidden="true" />
            Dashboard
          </a>

          <a className="navigation__item" href="#inventory">
            <Boxes size={19} aria-hidden="true" />
            Inventory
            <span className="navigation__count">{inventory.length}</span>
          </a>

          <a className="navigation__item" href="#alerts">
            <AlertTriangle size={19} aria-hidden="true" />
            Stock alerts
            <span className="navigation__count navigation__count--alert">
              {lowStockCount + outOfStockCount}
            </span>
          </a>

          <a className="navigation__item" href="#audit">
            <ClipboardList size={19} aria-hidden="true" />
            Audit log
          </a>

          <p className="navigation__label navigation__label--secondary">
            Administration
          </p>

          <a className="navigation__item" href="#security">
            <ShieldCheck size={19} aria-hidden="true" />
            Access control
          </a>

          <a className="navigation__item" href="#settings">
            <Settings size={19} aria-hidden="true" />
            Settings
          </a>
        </nav>

        <div className="sidebar__profile">
          <div className="avatar">OA</div>
          <div>
            <strong>Olawale Azeez</strong>
            <span>Platform administrator</span>
          </div>
          <ChevronDown size={17} aria-hidden="true" />
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button
            className="icon-button menu-button"
            type="button"
            aria-label="Toggle navigation"
            onClick={() => setMobileNavOpen((current) => !current)}
          >
            <Menu size={21} />
          </button>

          <div className="environment">
            <span className="environment__dot" />
            <div>
              <small>Environment</small>
              <strong>Production workspace</strong>
            </div>
          </div>

          <div className="topbar__actions">
            <button
              className="icon-button"
              type="button"
              aria-label="Notifications"
            >
              <Bell size={20} />
              <span className="notification-dot" />
            </button>

            <div className="topbar__identity">
              <UserRound size={18} aria-hidden="true" />
              <span>Hospital Central</span>
            </div>
          </div>
        </header>

        <div className="page" id="dashboard">
          <section className="page-heading">
            <div className="page-heading__copy">
              <p className="eyebrow">Pharmacy operations</p>
              <h1>Good afternoon, Olawale.</h1>
              <p>
                Here is today&apos;s inventory position across Hospital Central.
              </p>
            </div>

            <div className="page-heading__actions">
              <a className="secondary-button heading-link" href="#audit">
                <ClipboardList size={18} />
                View audit log
              </a>
              <button
                className="primary-button"
                type="button"
                onClick={() => {
                  setMedicineError('')
                  setMedicineSuccess('')
                  setAddMedicineOpen(true)
                }}
              >
                <CirclePlus size={19} />
                Add medicine
              </button>
            </div>
          </section>

          {medicineSuccess && (
            <div className="success-banner" role="status">
              <PackageCheck aria-hidden="true" size={19} />
              {medicineSuccess}
            </div>
          )}

          <section className="metric-grid" aria-label="Inventory summary">
            <MetricCard
              label="Total medicines"
              value={inventory.length.toString()}
              detail={`${totalUnits} units available`}
              icon={<Boxes size={21} />}
              tone="neutral"
            />

            <MetricCard
              label="Healthy stock"
              value={healthyCount.toString()}
              detail="No action required"
              icon={<PackageCheck size={21} />}
              tone="success"
            />

            <MetricCard
              label="Low stock"
              value={lowStockCount.toString()}
              detail="Reorder recommended"
              icon={<AlertTriangle size={21} />}
              tone="warning"
            />

            <MetricCard
              label="Out of stock"
              value={outOfStockCount.toString()}
              detail="Immediate action"
              icon={<XCircle size={21} />}
              tone="danger"
            />
          </section>

          <section className="inventory-panel" id="inventory">
            <div className="panel-heading">
              <div>
                <h2>Medicine inventory</h2>
                <p>Live operational view of medicines and stock thresholds.</p>
              </div>

              <span
                className={`data-mode data-mode--${dataSource}`}
                title={dataMessage}
              >
                <span />
                {dataSource === 'api'
                  ? 'Live API data'
                  : 'Local demonstration data'}
              </span>
            </div>

            <div className="toolbar">
              <label className="search-field">
                <Search size={18} aria-hidden="true" />
                <span className="sr-only">Search inventory</span>
                <input
                  type="search"
                  value={search}
                  placeholder="Search medicine, batch, or supplier"
                  onChange={(event) => setSearch(event.target.value)}
                />
              </label>

              <label className="filter-field">
                <span className="sr-only">Filter by stock status</span>
                <select
                  value={filter}
                  onChange={(event) =>
                    setFilter(event.target.value as FilterValue)
                  }
                >
                  <option value="All">All stock levels</option>
                  <option value="Healthy">Healthy</option>
                  <option value="Low stock">Low stock</option>
                  <option value="Out of stock">Out of stock</option>
                </select>
                <ChevronDown size={17} aria-hidden="true" />
              </label>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Medicine</th>
                    <th>Batch</th>
                    <th>Stock</th>
                    <th>Status</th>
                    <th>Expiry</th>
                    <th>Location</th>
                    <th>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredInventory.map((item) => {
                    const status = getStockStatus(item)

                    return (
                      <tr key={item.id}>
                        <td>
                          <div className="medicine-cell">
                            <div className="medicine-icon">
                              {item.drugName.slice(0, 1)}
                            </div>

                            <div>
                              <strong>{item.drugName}</strong>
                              <span>{item.category}</span>
                            </div>
                          </div>
                        </td>

                        <td>
                          <span className="batch-number">
                            {item.batchNumber}
                          </span>
                          <small>{item.supplier}</small>
                        </td>

                        <td>
                          <strong>{item.quantity}</strong>
                          <small>Reorder at {item.reorderLevel}</small>
                        </td>

                        <td>
                          <StatusBadge status={status} />
                        </td>

                        <td>{formatDate(item.expiryDate)}</td>

                        <td>
                          <span className="location-badge">
                            {item.location}
                          </span>
                        </td>

                        <td>
                          <button
                            className="table-action-button"
                            type="button"
                            onClick={() => {
                              setAdjustmentError('')
                              setSelectedMedicine(item)
                            }}
                          >
                            Adjust stock
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>

              {filteredInventory.length === 0 && (
                <div className="empty-state">
                  <Search size={25} />
                  <strong>No medicines found</strong>
                  <p>Try changing your search or stock filter.</p>
                </div>
              )}
            </div>

            <footer className="panel-footer">
              Showing {filteredInventory.length} of {inventory.length} medicines
            </footer>
          </section>

          <section className="audit-panel" id="audit">
            <div className="panel-heading">
              <div>
                <h2>Stock adjustment audit log</h2>
                <p>Immutable history of receipts, dispensing, corrections, and quarantines.</p>
              </div>
              <span className="audit-count">{auditHistory.length} records</span>
            </div>

            {auditHistory.length === 0 ? (
              <div className="audit-empty-state">
                <ClipboardList aria-hidden="true" size={26} />
                <strong>No stock adjustments recorded</strong>
                <p>Completed live API adjustments will appear here.</p>
              </div>
            ) : (
              <div className="table-wrapper">
                <table className="audit-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Medicine</th>
                      <th>Operation</th>
                      <th>Change</th>
                      <th>Stock</th>
                      <th>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditHistory.map((entry) => (
                      <tr key={entry.id}>
                        <td>{formatDateTime(entry.createdAt)}</td>
                        <td><strong>{entry.drugName}</strong><small>{entry.batchNumber}</small></td>
                        <td><span className={`operation-badge operation-badge--${entry.adjustmentType.toLowerCase()}`}>{formatAdjustmentType(entry.adjustmentType)}</span></td>
                        <td className={entry.quantityChange > 0 ? 'quantity-positive' : 'quantity-negative'}>
                          {entry.quantityChange > 0 ? '+' : ''}{entry.quantityChange}
                        </td>
                        <td>{entry.previousQuantity} → {entry.newQuantity}</td>
                        <td className="audit-reason">{entry.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </main>

      {addMedicineOpen && (
        <AddMedicineModal
          error={medicineError}
          isOpen
          isSubmitting={submittingMedicine}
          onClose={() => {
            setAddMedicineOpen(false)
            setMedicineError('')
          }}
          onSubmit={handleAddMedicine}
        />
      )}

      {selectedMedicine && (
        <StockAdjustmentModal
          error={adjustmentError}
          isSubmitting={submittingAdjustment}
          medicine={selectedMedicine}
          onClose={() => {
            setSelectedMedicine(null)
            setAdjustmentError('')
          }}
          onSubmit={handleStockAdjustment}
        />
      )}
    </div>
  )
}

interface MetricCardProps {
  label: string
  value: string
  detail: string
  icon: React.ReactNode
  tone: 'neutral' | 'success' | 'warning' | 'danger'
}

function MetricCard({
  label,
  value,
  detail,
  icon,
  tone,
}: MetricCardProps) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <div className="metric-card__top">
        <span>{label}</span>
        <div className="metric-card__icon">{icon}</div>
      </div>

      <strong className="metric-card__value">{value}</strong>
      <p>{detail}</p>
    </article>
  )
}

function StatusBadge({ status }: { status: StockStatus }) {
  const className = status.toLowerCase().replaceAll(' ', '-')

  return (
    <span className={`status-badge status-badge--${className}`}>
      <span />
      {status}
    </span>
  )
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value))
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('en-GB', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatAdjustmentType(value: AuditEntry['adjustmentType']) {
  return {
    RECEIPT: 'Received',
    DISPENSE: 'Dispensed',
    CORRECTION: 'Corrected',
    QUARANTINE: 'Quarantined',
  }[value]
}

export default App
