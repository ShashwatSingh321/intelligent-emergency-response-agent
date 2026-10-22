import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity, AlertCircle, AlertTriangle, ArrowDownRight, ArrowRight,
  ArrowUpRight, Bell, Check, ChevronDown, Clock3, Command, Compass,
  HeartPulse, LayoutDashboard, MapPin, Menu, MessageSquareText,
  Plus, RefreshCw, Search, Send, ShieldCheck, Siren, Stethoscope,
  Users, X, Zap, Building2, PackageSearch, Route, Radio,
} from 'lucide-react'
import './App.css'

const API = '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(body?.detail || body?.message || `Request failed (${response.status})`)
  }
  return body
}

function asArray(value) {
  if (Array.isArray(value)) return value
  if (Array.isArray(value?.items)) return value.items
  if (Array.isArray(value?.emergencies)) return value.emergencies
  return []
}

function readable(value) {
  return String(value ?? 'Unknown').replaceAll('_', ' ').toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function timeLabel(value) {
  if (!value) return 'Time not recorded'
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function getId(item) {
  return item?.report_id ?? item?.id ?? item?.emergency_id ?? '—'
}

function getLocation(item, locations = []) {
  const id = item?.location_id ?? item?.location ?? item?.location_name
  const found = locations.find((place) => place.id === id || place.name === id)
  return found?.name ?? readable(id ?? 'Location not provided')
}

function priorityClass(value) {
  const priority = String(value ?? '').toLowerCase()
  if (priority.includes('critical') || priority.includes('high')) return 'priority-high'
  if (priority.includes('medium') || priority.includes('moderate')) return 'priority-medium'
  return 'priority-low'
}

const ALLOWED_TRANSITIONS = {
  reported: ['under_review', 'cancelled'],
  under_review: ['assigned', 'cancelled'],
  assigned: ['responding', 'cancelled'],
  responding: ['resolved', 'cancelled'],
  resolved: [],
  cancelled: [],
}

const navItems = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'report', label: 'Report emergency', icon: Siren },
  { id: 'ambulances', label: 'Request ambulances', icon: Radio },
  { id: 'incidents', label: 'Incident records', icon: Activity },
  { id: 'campus', label: 'Campus directory', icon: Compass },
]

function App() {
  const [page, setPage] = useState('overview')
  const [incidents, setIncidents] = useState([])
  const [locations, setLocations] = useState([])
  const [facilities, setFacilities] = useState([])
  const [loading, setLoading] = useState(true)
  const [apiOnline, setApiOnline] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [search, setSearch] = useState('')
  const [facilitySearch, setFacilitySearch] = useState('')
  const [selectedLocation, setSelectedLocation] = useState('all')
  const [mobileNav, setMobileNav] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [reportText, setReportText] = useState('')
  const [lastResult, setLastResult] = useState(null)
  const [selectedIncident, setSelectedIncident] = useState(null)

  // ── Status history state ──────────────────────────────────────────
  const [statusHistory, setStatusHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  // ──────────────────────────────────────────────────────────────────

  // ── Ambulance request state ───────────────────────────────────────
  const [ambulanceRequests, setAmbulanceRequests] = useState([])
  const [ambulanceLocationId, setAmbulanceLocationId] = useState('')
  const [ambulanceCount, setAmbulanceCount] = useState('1')
  const [ambulanceReason, setAmbulanceReason] = useState('')
  const [ambulanceSubmitting, setAmbulanceSubmitting] = useState(false)
  const [ambulanceLoading, setAmbulanceLoading] = useState(false)
  // ──────────────────────────────────────────────────────────────────

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    const results = await Promise.allSettled([
      request('/emergencies'),
      request('/campus/locations'),
      request('/campus/facilities'),
    ])
    const [emergencyResult, locationResult, facilityResult] = results
    if (emergencyResult.status === 'fulfilled') {
      setIncidents(asArray(emergencyResult.value))
      setApiOnline(true)
    } else {
      setApiOnline(false)
      setError(`Could not load incident records: ${emergencyResult.reason.message}`)
    }
    if (locationResult.status === 'fulfilled') setLocations(asArray(locationResult.value))
    if (facilityResult.status === 'fulfilled') setFacilities(asArray(facilityResult.value))
    setLoading(false)
  }, [])

  useEffect(() => { loadData() }, [loadData])

  // ── Ambulance request loading & submission ────────────────────────
  const loadAmbulanceRequests = useCallback(async () => {
    setAmbulanceLoading(true)
    try {
      const data = await request('/ambulance-requests')
      setAmbulanceRequests(asArray(data))
    } catch (err) {
      setError(`Could not load ambulance requests: ${err.message}`)
    } finally {
      setAmbulanceLoading(false)
    }
  }, [])

  const submitAmbulanceRequest = async (event) => {
    event.preventDefault()
    setAmbulanceSubmitting(true)
    setError('')
    setNotice('')

    try {
      const result = await request('/ambulance-requests', {
        method: 'POST',
        body: JSON.stringify({
          location_id: ambulanceLocationId,
          ambulance_count: Number(ambulanceCount),
          reason: ambulanceReason.trim(),
        }),
      })

      setNotice(
        `Request ${result.request_id} saved. Email status: ${readable(result.notification_status)}.`
      )
      setAmbulanceCount('1')
      setAmbulanceReason('')
      await loadAmbulanceRequests()
    } catch (err) {
      setError(`Could not submit ambulance request: ${err.message}`)
    } finally {
      setAmbulanceSubmitting(false)
    }
  }

  useEffect(() => {
    if (page === 'ambulances') {
      loadAmbulanceRequests()
    }
  }, [page, loadAmbulanceRequests])
  // ──────────────────────────────────────────────────────────────────

  const filteredIncidents = useMemo(() => incidents.filter((item) => {
    const query = search.trim().toLowerCase()
    const matchesSearch = !query || [
      getId(item), item.description, item.emergency_type, item.location_id,
      item.status, item.priority,
    ].some((value) => String(value ?? '').toLowerCase().includes(query))
    const matchesLocation = selectedLocation === 'all' || item.location_id === selectedLocation
    return matchesSearch && matchesLocation
  }), [incidents, search, selectedLocation])

  const activeCount = incidents.filter((item) => {
    const status = String(item.status ?? '').toLowerCase()
    return !['resolved', 'closed', 'completed'].includes(status)
  }).length

  const highPriorityCount = incidents.filter((item) => {
    const p = String(item.priority ?? '').toLowerCase()
    return p.includes('critical') || p.includes('high')
  }).length

  const filteredFacilities = facilities.filter((facility) => {
    const query = facilitySearch.trim().toLowerCase()
    const matchesText = !query || [
      facility.name, facility.details, facility.location_name, facility.location_id,
    ].some((value) => String(value ?? '').toLowerCase().includes(query))
    const matchesLocation = selectedLocation === 'all' || facility.location_id === selectedLocation
    return matchesText && matchesLocation
  })

  async function submitReport(event) {
    event.preventDefault()
    if (!reportText.trim()) return
    setSubmitting(true)
    setError('')
    setNotice('')
    setLastResult(null)
    try {
      const result = await request('/emergencies/from-text', {
        method: 'POST',
        body: JSON.stringify({ text: reportText.trim() }),
      })
      setLastResult(result)
      setNotice('Your report was received by the backend.')
      setReportText('')
      await loadData()
    } catch (err) {
      setError(`Report could not be submitted: ${err.message}`)
    } finally {
      setSubmitting(false)
    }
  }

  async function updateStatus(item, status) {
    const id = getId(item)
    if (id === '—') return
    setError('')
    setNotice('')
    try {
      await request(`/emergencies/${encodeURIComponent(id)}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      })
      setNotice(`Incident ${id} status updated.`)
      setSelectedIncident(null)
      await loadData()
    } catch (err) {
      setError(`Status update failed: ${err.message}. Check the status values supported by your backend.`)
    }
  }

  // ── Open incident + load its history ──────────────────────────────
  async function openIncident(item) {
    setSelectedIncident(item)
    setStatusHistory([])
    setHistoryLoading(true)

    try {
      const history = await request(
        `/emergencies/${encodeURIComponent(getId(item))}/history`
      )
      setStatusHistory(asArray(history))
    } catch (err) {
      setError(`Could not load status history: ${err.message}`)
    } finally {
      setHistoryLoading(false)
    }
  }
  // ──────────────────────────────────────────────────────────────────

  async function searchFacilities(event) {
    event?.preventDefault()
    setError('')
    if (!facilitySearch.trim()) {
      try {
        setFacilities(asArray(await request('/campus/facilities')))
      } catch (err) {
        setError(err.message)
      }
      return
    }
    try {
      const result = await request(`/campus/facilities/search?q=${encodeURIComponent(facilitySearch.trim())}`)
      setFacilities(asArray(result))
    } catch (err) {
      setError(`Facility search failed: ${err.message}`)
    }
  }

  function navigate(nextPage) {
    setPage(nextPage)
    setMobileNav(false)
    setError('')
    setNotice('')
  }

  const pageTitle = navItems.find((item) => item.id === page)?.label ?? 'Overview'

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><HeartPulse size={24} strokeWidth={2.4} /></div>
          <div className="brand-copy">
            <strong>ResQ<span>AI</span></strong>
            <small>EMERGENCY RESPONSE</small>
          </div>
          <button className="icon-button mobile-close" onClick={() => setMobileNav(false)} aria-label="Close menu"><X /></button>
        </div>

        <div className="workspace-label">WORKSPACE</div>
        <nav className="side-nav" aria-label="Main navigation">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button key={id} className={`nav-item ${page === id ? 'nav-active' : ''}`} onClick={() => navigate(id)}>
              <Icon size={18} />
              <span>{label}</span>
              {id === 'report' && <span className="nav-plus"><Plus size={14} /></span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="help-card">
            <div className="help-icon"><ShieldCheck size={19} /></div>
            <strong>Response, coordinated.</strong>
            <p>One place for campus incident information and resources.</p>
            <button onClick={() => navigate('campus')}>Explore directory <ArrowRight size={14} /></button>
          </div>
          <div className="connection-line">
            <span className={`connection-dot ${apiOnline ? 'online' : ''}`} />
            <span>{apiOnline ? 'Backend connected' : 'Backend unavailable'}</span>
          </div>
          <div className="sidebar-foot">RESQAI <span>•</span> CAMPUS SAFETY</div>
        </div>
      </aside>

      {mobileNav && <button className="mobile-overlay" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button className="icon-button menu-toggle" onClick={() => setMobileNav(true)} aria-label="Open menu"><Menu /></button>
            <div className="breadcrumb">Workspace <span>/</span> <strong>{pageTitle}</strong></div>
          </div>
          <div className="topbar-right">
            <div className="system-state"><span className={`status-dot ${apiOnline ? 'green' : 'amber'}`} />{apiOnline ? 'System connected' : 'Waiting for backend'}</div>
            <button className="icon-button" onClick={loadData} title="Refresh data" aria-label="Refresh data"><RefreshCw size={17} /></button>
            <div className="avatar">ER</div>
          </div>
        </header>

        <div className="page-content">
          <div className="page-heading">
            <div>
              <div className="eyebrow"><span className="eyebrow-dot" /> CAMPUS OPERATIONS</div>
              <h1>{page === 'overview' ? 'Good day, response team' : pageTitle}<span className="heading-period">.</span></h1>
              <p className="page-subtitle">
                {page === 'overview' && 'A clear view of campus incidents, resources, and response activity.'}
                {page === 'report' && 'Share what happened in plain language. The agent will process your report.'}
                {page === 'ambulances' && 'Request additional ambulance resources and review previous requests.'}
                {page === 'incidents' && 'Review incident records and inspect the status returned by the backend.'}
                {page === 'campus' && 'Find campus locations and registered facilities from your local database.'}
              </p>
            </div>
            <div className="heading-actions">
              <button className="button button-secondary" onClick={loadData}><RefreshCw size={15} /> Refresh</button>
              <button className="button button-primary" onClick={() => navigate('report')}><Plus size={17} /> New report</button>
            </div>
          </div>

          {error && <div className="alert-banner alert-error"><AlertCircle size={18} /><span>{error}</span><button onClick={() => setError('')} aria-label="Dismiss error"><X size={16} /></button></div>}
          {notice && <div className="alert-banner alert-success"><Check size={18} /><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Dismiss notice"><X size={16} /></button></div>}

          {page === 'overview' && (
            <>
              <section className="welcome-strip">
                <div className="welcome-symbol"><Zap size={22} /></div>
                <div className="welcome-copy">
                  <strong>Every second matters. Every detail helps.</strong>
                  <span>Use the emergency report workflow to record an incident and let the backend process it.</span>
                </div>
                <button onClick={() => navigate('report')}>Report an incident <ArrowRight size={16} /></button>
                <div className="strip-decoration" />
              </section>

              <section className="metric-grid" aria-label="Incident summary">
                <Metric icon={Activity} label="Total incidents" value={loading ? '—' : incidents.length} note="Records from the API" tone="blue" />
                <Metric icon={Radio} label="Active incidents" value={loading ? '—' : activeCount} note="Not marked resolved" tone="orange" />
                <Metric icon={AlertTriangle} label="High priority" value={loading ? '—' : highPriorityCount} note="Based on recorded priority" tone="red" />
                <Metric icon={MapPin} label="Campus locations" value={loading ? '—' : locations.length} note="Loaded from campus data" tone="green" />
              </section>

              <section className="content-grid">
                <div className="panel incidents-panel">
                  <div className="panel-heading">
                    <div><h2>Recent incidents</h2><p>Live records returned by your backend</p></div>
                    <button className="text-link" onClick={() => navigate('incidents')}>View all <ArrowRight size={15} /></button>
                  </div>
                  <IncidentTable items={incidents.slice(0, 5)} locations={locations} loading={loading} onSelect={openIncident} />
                  {!loading && incidents.length === 0 && <EmptyState icon={ShieldCheck} title="A clear dashboard" text="No incident records were returned. Submit a test report to see the workflow in action." action="Create a report" onAction={() => navigate('report')} />}
                </div>

                <div className="right-stack">
                  <div className="panel readiness-panel">
                    <div className="panel-heading"><div><h2>System status</h2><p>Connection health</p></div><span className={`tiny-status ${apiOnline ? 'healthy' : 'waiting'}`}>{apiOnline ? 'Connected' : 'Offline'}</span></div>
                    <div className="system-row"><span className="system-icon purple"><Activity size={17} /></span><div><strong>Emergency API</strong><small>Incident records endpoint</small></div><span className={`status-dot ${apiOnline ? 'green' : 'amber'}`} /></div>
                    <div className="system-row"><span className="system-icon teal"><Building2 size={17} /></span><div><strong>Campus directory</strong><small>{locations.length} locations loaded</small></div><span className={`status-dot ${locations.length ? 'green' : 'amber'}`} /></div>
                    <div className="system-row"><span className="system-icon orange"><PackageSearch size={17} /></span><div><strong>Facility database</strong><small>{facilities.length} facilities loaded</small></div><span className={`status-dot ${facilities.length ? 'green' : 'amber'}`} /></div>
                    <div className="panel-footnote"><ShieldCheck size={14} /> Status reflects the latest API request.</div>
                  </div>

                  <div className="panel campus-panel">
                    <div className="panel-heading"><div><h2>Campus locations</h2><p>Configured in your campus map</p></div><button className="icon-button small" onClick={() => navigate('campus')} aria-label="Open campus directory"><ArrowRight size={16} /></button></div>
                    {locations.length ? locations.slice(0, 5).map((location, index) => (
                      <div className="location-row" key={location.id ?? index}>
                        <span className={`location-symbol location-${index % 4}`}><MapPin size={16} /></span>
                        <div><strong>{location.name ?? readable(location.id)}</strong><small>{location.id ?? 'Campus location'}</small></div>
                      </div>
                    )) : <p className="muted-copy">{loading ? 'Loading campus locations…' : 'No campus locations available.'}</p>}
                    <button className="full-width-link" onClick={() => navigate('campus')}>Open campus directory <ArrowRight size={15} /></button>
                  </div>
                </div>
              </section>
            </>
          )}

          {page === 'report' && (
            <section className="report-layout">
              <div className="panel report-panel">
                <div className="panel-heading report-title">
                  <div><div className="form-icon"><MessageSquareText size={21} /></div><h2>Describe the emergency</h2><p>Use plain language, including the place and what help is needed.</p></div>
                  <span className="step-chip">STEP 01</span>
                </div>
                <form onSubmit={submitReport}>
                  <label className="field-label" htmlFor="report-description">Incident description <span>Required</span></label>
                  <textarea id="report-description" className="report-textarea" value={reportText} onChange={(e) => setReportText(e.target.value)} placeholder="Example: Someone has fallen near the Central Library and needs medical assistance…" rows={7} required maxLength={2000} />
                  <div className="textarea-footer"><span>Include location, incident type, and immediate needs if known.</span><span>{reportText.length}/2000</span></div>
                  <div className="privacy-note"><ShieldCheck size={16} /><span>Submit factual information. The application processes this through your local backend; verify the result before taking real-world action.</span></div>
                  <button className="button button-primary submit-button" type="submit" disabled={submitting || !reportText.trim()}>
                    {submitting ? <><RefreshCw size={17} className="spin" /> Processing report…</> : <><Send size={17} /> Submit emergency report</>}
                  </button>
                </form>
                {lastResult && (
                  <div className="result-card">
                    <div className="result-header"><Check size={18} /><strong>Backend response received</strong></div>
                    <div className="result-grid">
                      <Result label="Report ID" value={getId(lastResult)} />
                      <Result label="Emergency type" value={readable(lastResult.emergency_type)} />
                      <Result label="Location" value={getLocation(lastResult, locations)} />
                      <Result label="Priority" value={readable(lastResult.priority)} />
                      <Result label="Status" value={readable(lastResult.status)} />
                      <Result label="Route cost" value={lastResult.route_cost ?? 'Not provided'} />
                    </div>
                    {lastResult.priority_explanation && <p className="result-explanation">{lastResult.priority_explanation}</p>}
                    {lastResult.recommendation && <p className="result-explanation"><strong>Recommendation:</strong> {lastResult.recommendation}</p>}

                    {/* ── Ambulance & email notification details ── */}
                    <div className="response-details">
                      <section className="response-detail">
                        <h3><Siren size={17} /> Ambulance recommendation</h3>

                        {lastResult.ambulance ? (
                          <>
                            <p>
                              <strong>Ambulance:</strong>{' '}
                              {lastResult.ambulance.id}
                            </p>
                            <p>
                              <strong>Starting location:</strong>{' '}
                              {getLocation(
                                { location_id: lastResult.ambulance.starting_location },
                                locations
                              )}
                            </p>
                          </>
                        ) : (
                          <p>No suitable ambulance was assigned by the backend.</p>
                        )}
                      </section>

                      <section className="response-detail">
                        <h3><Bell size={17} /> Email notification</h3>
                        <p>
                          <span className={`notification-state notification-${String(lastResult.email_notification ?? 'unknown').toLowerCase()}`}>
                            {readable(lastResult.email_notification ?? 'Not reported')}
                          </span>
                        </p>
                        <p className="muted-copy">
                          This is the notification result for this submission.
                        </p>
                      </section>
                    </div>

                    {/* ── Route visualization ── */}
                    <section className="route-visual">
                      <h3><Route size={17} /> Recommended campus route</h3>

                      {Array.isArray(lastResult.route) && lastResult.route.length > 0 ? (
                        <div className="route-steps">
                          {lastResult.route.map((stop, index) => (
                            <div className="route-step" key={`${stop}-${index}`}>
                              <span className="route-step-number">{index + 1}</span>
                              <div>
                                <strong>
                                  {getLocation({ location_id: stop }, locations)}
                                </strong>
                                <small>
                                  {index === 0
                                    ? 'Starting point'
                                    : index === lastResult.route.length - 1
                                      ? 'Emergency destination'
                                      : 'Next stop'}
                                </small>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="muted-copy">
                          No route was returned. Check whether a suitable ambulance and connected path were available.
                        </p>
                      )}

                      {lastResult.route_cost != null && (
                        <p className="route-cost">
                          Route cost: <strong>{lastResult.route_cost}</strong>
                        </p>
                      )}
                    </section>

                    <pre className="json-preview">{JSON.stringify(lastResult, null, 2)}</pre>
                  </div>
                )}
              </div>
              <aside className="report-side">
                <div className="panel guidance-panel">
                  <div className="guidance-icon"><HeartPulse size={22} /></div>
                  <h2>Help the agent understand</h2>
                  <p>A useful report is specific and direct. Only include details you know.</p>
                  <div className="guidance-item"><span>01</span><div><strong>Where is it?</strong><p>Give a campus building or known location.</p></div></div>
                  <div className="guidance-item"><span>02</span><div><strong>What happened?</strong><p>Describe the incident without guessing.</p></div></div>
                  <div className="guidance-item"><span>03</span><div><strong>What help is needed?</strong><p>Share urgent needs or the number of people affected, if known.</p></div></div>
                </div>
                <div className="safety-card"><AlertTriangle size={18} /><div><strong>Real emergency?</strong><p>Contact local emergency services immediately. This student project is not a substitute for verified emergency dispatch.</p></div></div>
              </aside>
            </section>
          )}

          {page === 'ambulances' && (
            <section className="ambulance-page">
              <div className="panel full-panel">
                <div className="panel-heading">
                  <div>
                    <h2>Request additional ambulances</h2>
                    <p>Submit a resource request for a campus location.</p>
                  </div>
                  <Radio size={22} />
                </div>

                <form className="ambulance-form" onSubmit={submitAmbulanceRequest}>
                  <label className="field-label" htmlFor="ambulance-location">
                    Campus building
                  </label>
                  <select
                    id="ambulance-location"
                    value={ambulanceLocationId}
                    onChange={(event) => setAmbulanceLocationId(event.target.value)}
                    required
                  >
                    <option value="">Select a building or location</option>
                    {locations.map((location) => (
                      <option key={location.id} value={location.id}>
                        {location.name}
                      </option>
                    ))}
                  </select>

                  <label className="field-label" htmlFor="ambulance-count">
                    Additional ambulances required
                  </label>
                  <input
                    id="ambulance-count"
                    type="number"
                    min="1"
                    max="20"
                    step="1"
                    value={ambulanceCount}
                    onChange={(event) => setAmbulanceCount(event.target.value)}
                    required
                  />

                  <label className="field-label" htmlFor="ambulance-reason">
                    Reason for the request
                  </label>
                  <textarea
                    id="ambulance-reason"
                    value={ambulanceReason}
                    onChange={(event) => setAmbulanceReason(event.target.value)}
                    placeholder="Explain why additional ambulances are needed..."
                    minLength={3}
                    maxLength={1000}
                    required
                  />

                  <button
                    className="button button-primary"
                    type="submit"
                    disabled={ambulanceSubmitting || locations.length === 0}
                  >
                    <Send size={16} />
                    {ambulanceSubmitting ? 'Submitting request...' : 'Submit ambulance request'}
                  </button>
                </form>
              </div>

              <div className="panel full-panel">
                <div className="panel-heading">
                  <div>
                    <h2>Previous ambulance requests</h2>
                    <p>{ambulanceRequests.length} saved requests</p>
                  </div>
                  <button
                    className="button button-secondary"
                    onClick={loadAmbulanceRequests}
                    disabled={ambulanceLoading}
                  >
                    <RefreshCw size={15} /> Refresh
                  </button>
                </div>

                {ambulanceLoading ? (
                  <p className="ambulance-empty">Loading requests...</p>
                ) : ambulanceRequests.length === 0 ? (
                  <p className="ambulance-empty">No additional ambulance requests yet.</p>
                ) : (
                  <div className="ambulance-request-list">
                    {ambulanceRequests.map((item) => (
                      <article className="ambulance-request-card" key={item.request_id}>
                        <div className="ambulance-request-heading">
                          <strong>{item.request_id}</strong>
                          <span className={`notification-${item.notification_status}`}>
                            {readable(item.notification_status)}
                          </span>
                        </div>
                        <p><strong>Location:</strong> {item.location_name}</p>
                        <p><strong>Ambulances requested:</strong> {item.ambulance_count}</p>
                        <p><strong>Reason:</strong> {item.reason}</p>
                        <small>{timeLabel(item.created_at)}</small>
                      </article>
                    ))}
                  </div>
                )}

                <p className="directory-disclaimer">
                  <AlertCircle size={15} />
                  Email status does not confirm authority acknowledgement or ambulance dispatch.
                </p>
              </div>
            </section>
          )}

          {page === 'incidents' && (
            <section className="panel full-panel">
              <div className="panel-heading">
                <div><h2>Incident records</h2><p>{incidents.length} records currently returned by the API</p></div>
                <button className="button button-secondary" onClick={loadData}><RefreshCw size={15} /> Refresh records</button>
              </div>
              <div className="filter-row">
                <div className="search-box"><Search size={17} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search description, ID, type…" /></div>
                <select aria-label="Filter by location" value={selectedLocation} onChange={(e) => setSelectedLocation(e.target.value)}><option value="all">All locations</option>{locations.map((loc) => <option key={loc.id} value={loc.id}>{loc.name}</option>)}</select>
              </div>
              <IncidentTable items={filteredIncidents} locations={locations} loading={loading} onSelect={openIncident} />
              {!loading && filteredIncidents.length === 0 && <EmptyState icon={Search} title="No matching incidents" text="Try changing the search or location filter." action="Clear filters" onAction={() => { setSearch(''); setSelectedLocation('all') }} />}
            </section>
          )}

          {page === 'campus' && (
            <section className="campus-directory">
              <div className="panel full-panel">
                <div className="panel-heading">
                  <div><h2>Campus directory</h2><p>Locations and facilities available in the local database</p></div>
                  <span className="directory-count"><MapPin size={15} /> {locations.length} locations</span>
                </div>
                <div className="filter-row">
                  <form className="search-box facility-search" onSubmit={searchFacilities}><Search size={17} /><input value={facilitySearch} onChange={(e) => setFacilitySearch(e.target.value)} placeholder="Search first aid, security, building…" /><button type="submit" aria-label="Search facilities"><ArrowRight size={16} /></button></form>
                  <select aria-label="Filter campus location" value={selectedLocation} onChange={(e) => setSelectedLocation(e.target.value)}><option value="all">All locations</option>{locations.map((loc) => <option key={loc.id} value={loc.id}>{loc.name}</option>)}</select>
                </div>
                <div className="directory-grid">
                  {locations.filter((loc) => selectedLocation === 'all' || loc.id === selectedLocation).map((location, index) => {
                    const locationFacilities = filteredFacilities.filter((f) => f.location_id === location.id)
                    return <div className="directory-card" key={location.id}>
                      <div className={`directory-card-icon location-${index % 4}`}><Building2 size={20} /></div>
                      <div className="directory-card-title"><h3>{location.name}</h3><span>{location.id}</span></div>
                      <div className="directory-card-divider" />
                      <div className="facility-card-label"><PackageSearch size={15} /> Registered facilities <span>{locationFacilities.length}</span></div>
                      {locationFacilities.length ? locationFacilities.map((facility) => <div className="facility-item" key={facility.id}><Stethoscope size={15} /><div><strong>{facility.name}</strong><small>{facility.details || 'No additional details recorded'}</small></div></div>) : <div className="facility-empty">No matching facilities recorded.</div>}
                    </div>
                  })}
                </div>
                {!locations.length && <EmptyState icon={Compass} title="Campus data unavailable" text="Check that the FastAPI server is running and the campus endpoint is accessible." action="Retry" onAction={loadData} />}
                <p className="directory-disclaimer"><AlertCircle size={15} /> Only facilities stored in the database are shown. Their presence does not confirm current availability.</p>
              </div>
            </section>
          )}

          <footer className="page-footer"><span>ResQAI <span className="footer-dot">•</span> Intelligent Emergency Response Agent</span><span><ShieldCheck size={13} /> Local development environment</span></footer>
        </div>
      </main>

      {selectedIncident && <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) setSelectedIncident(null) }}>
        <section className="incident-modal" role="dialog" aria-modal="true" aria-labelledby="incident-modal-title">
          <div className="modal-heading"><div><span className="eyebrow">INCIDENT DETAILS</span><h2 id="incident-modal-title">Report #{getId(selectedIncident)}</h2></div><button className="icon-button" onClick={() => setSelectedIncident(null)} aria-label="Close details"><X /></button></div>
          <div className="modal-description">{selectedIncident.description || 'No description recorded.'}</div>
          <div className="modal-facts">
            <Result label="Type" value={readable(selectedIncident.emergency_type)} />
            <Result label="Location" value={getLocation(selectedIncident, locations)} />
            <Result label="Priority" value={readable(selectedIncident.priority)} />
            <Result label="Status" value={readable(selectedIncident.status)} />
            <Result label="People affected" value={selectedIncident.people_affected ?? 'Not recorded'} />
          </div>
          {selectedIncident.priority_explanation && <p className="result-explanation">{selectedIncident.priority_explanation}</p>}

          {/* ── Status history timeline ── */}
          <section className="history-section">
            <h3><Clock3 size={17} /> Status history</h3>

            {historyLoading ? (
              <p className="muted-copy">Loading status history...</p>
            ) : statusHistory.length ? (
              <div className="history-timeline">
                {statusHistory.map((entry, index) => (
                  <div
                    className="history-entry"
                    key={`${entry.report_id}-${entry.changed_at}-${index}`}
                  >
                    <span className="history-marker" />
                    <div>
                      <strong>
                        {readable(entry.previous_status)} → {readable(entry.new_status)}
                      </strong>
                      <small>{timeLabel(entry.changed_at)}</small>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted-copy">
                No status changes have been recorded for this incident yet.
              </p>
            )}
          </section>

          <label className="field-label" htmlFor="status-update">
            Update status
          </label>

          <select
            id="status-update"
            className="status-select"
            defaultValue=""
            disabled={
              (ALLOWED_TRANSITIONS[
                String(selectedIncident.status ?? '').toLowerCase()
              ] ?? []).length === 0
            }
            onChange={(e) => {
              const nextStatus = e.target.value
              if (nextStatus) {
                updateStatus(selectedIncident, nextStatus)
              }
            }}
          >
            <option value="" disabled>
              {(ALLOWED_TRANSITIONS[
                String(selectedIncident.status ?? '').toLowerCase()
              ] ?? []).length > 0
                ? 'Choose a valid next status…'
                : 'No further transitions available'}
            </option>

            {(ALLOWED_TRANSITIONS[
              String(selectedIncident.status ?? '').toLowerCase()
            ] ?? []).map((status) => (
              <option key={status} value={status}>
                {readable(status)}
              </option>
            ))}
          </select>

          <p className="modal-hint">
            Only transitions permitted by the backend are offered.
            Resolved and cancelled incidents cannot be advanced further.
          </p>
        </section>
      </div>}
    </div>
  )
}

function Metric({ icon: Icon, label, value, note, tone }) {
  return <div className="metric-card"><div className={`metric-icon metric-${tone}`}><Icon size={20} /></div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-note">{note}</div></div>
}

function Result({ label, value }) {
  return <div className="result-field"><span>{label}</span><strong>{String(value ?? 'Not recorded')}</strong></div>
}

function EmptyState({ icon: Icon, title, text, action, onAction }) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={23} /></div><h3>{title}</h3><p>{text}</p>{action && <button className="button button-secondary" onClick={onAction}>{action} <ArrowRight size={15} /></button>}</div>
}

function IncidentTable({ items, locations, loading, onSelect }) {
  if (loading) return <div className="table-loading"><span className="spinner" /> Loading incident records…</div>
  if (!items.length) return null
  return <div className="table-scroll"><table className="incident-table"><thead><tr><th>Incident</th><th>Location</th><th>Priority</th><th>Status</th><th>Reported</th><th /></tr></thead>
    <tbody>{items.map((item, index) => <tr key={getId(item) === '—' ? index : getId(item)} onClick={() => onSelect(item)} tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter') onSelect(item) }}>
      <td><div className="incident-id">#{getId(item)}</div><div className="incident-description">{item.description || readable(item.emergency_type)}</div></td>
      <td><div className="table-location"><MapPin size={14} />{getLocation(item, locations)}</div></td>
      <td><span className={`priority-pill ${priorityClass(item.priority)}`}><span />{readable(item.priority)}</span></td>
      <td><span className="status-pill">{readable(item.status)}</span></td>
      <td className="date-cell">{timeLabel(item.created_at ?? item.reported_at ?? item.timestamp)}</td>
      <td><ArrowRight size={16} className="row-arrow" /></td>
    </tr>)}</tbody></table></div>
}

export default App