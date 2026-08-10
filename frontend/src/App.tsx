import { useMemo, useState } from 'react'
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
import { mockInventory } from './data/mockInventory'
import {
  getStockStatus,
  type InventoryItem,
  type StockStatus,
} from './types/inventory'

type FilterValue = 'All' | StockStatus

function App() {
  const [inventory] = useState<InventoryItem[]>(mockInventory)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<FilterValue>('All')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

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

          <a className="navigation__item navigation__item--active" href="#dashboard">
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
            Production environment
          </div>

          <div className="topbar__actions">
            <button className="icon-button" type="button" aria-label="Notifications">
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
            <div>
              <p className="eyebrow">Pharmacy operations</p>
              <h1>Inventory dashboard</h1>
              <p>
                Monitor medicine availability, identify supply risks, and keep
                clinical teams ready.
              </p>
            </div>

            <button className="primary-button" type="button">
              <CirclePlus size={19} />
              Add medicine
            </button>
          </section>

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

              <span className="data-mode">
                <span />
                Local demonstration data
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
                          <span className="batch-number">{item.batchNumber}</span>
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
                          <span className="location-badge">{item.location}</span>
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
        </div>
      </main>
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

function MetricCard({ label, value, detail, icon, tone }: MetricCardProps) {
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

export default App