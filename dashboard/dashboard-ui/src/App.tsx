import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Server,
  ShieldCheck,
  Database,
  BarChart3,
  Github,
  Cpu,
  Boxes,
  GitBranch,
  Activity,
  Cloud,
  Sun,
  Moon,
} from 'lucide-react'
import {
  CONCURRENCY,
  DATA,
  DEPLOYMENTS,
  METRICS,
  takeaway,
  type Coupling,
  type Metric,
} from './data/benchmarks'

const REPO_URL = 'https://github.com/HaoC916/Microservices-Game-Backend'

const SERVICES = [
  { name: 'Nakama', role: 'Game core', desc: 'Login, matchmaking, and realtime play.', icon: Server },
  { name: 'Admin', role: 'Control gate', desc: 'Sync or async gate before matchmaking.', icon: ShieldCheck },
  { name: 'EventHub', role: 'Event store', desc: 'Stores events in their own database.', icon: Database },
  { name: 'Dashboard', role: 'Service status', desc: 'Aggregates status across every service.', icon: BarChart3 },
]

const SETUP = [
  { icon: Boxes, label: 'Deployments', value: 'Single-VM · Multi-VM · GKE' },
  { icon: Cpu, label: 'Machine', value: 'e2-medium (2 vCPU, 4 GB)' },
  { icon: Activity, label: 'Concurrency', value: '25 → 150 virtual users' },
  { icon: GitBranch, label: 'Coupling', value: 'gate-on (sync) vs gate-off (async)' },
  { icon: Cloud, label: 'Cloud', value: 'Google Compute Engine, multi-zone' },
]

const VBW = 760
const VBH = 360
const M = { top: 22, right: 18, bottom: 44, left: 50 }
const PLOT_W = VBW - M.left - M.right
const PLOT_H = VBH - M.top - M.bottom

function niceBounds(values: number[]): [number, number] {
  const min = Math.min(...values)
  const max = Math.max(...values)
  const pad = Math.max((max - min) * 0.12, 4)
  const lo = Math.max(0, Math.floor((min - pad) / 10) * 10)
  const hi = Math.ceil((max + pad) / 10) * 10
  return [lo, hi]
}

function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof localStorage !== 'undefined') {
      const s = localStorage.getItem('bench-theme')
      if (s === 'light' || s === 'dark') return s
    }
    return 'dark'
  })
  const dark = theme === 'dark'

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    try {
      localStorage.setItem('bench-theme', theme)
    } catch {
      // ignore storage failures
    }
  }, [theme, dark])

  const [coupling, setCoupling] = useState<Coupling>('sync')
  const [metric, setMetric] = useState<Metric>('throughput')
  const [hover, setHover] = useState<number | null>(null)
  const svgRef = useRef<SVGSVGElement | null>(null)

  const meta = METRICS[metric]
  const series = DATA[metric][coupling]

  const C = dark
    ? { grid: '#1e293b', tick: '#64748b', axis: '#94a3b8', guide: '#475569', dot: '#0f172a' }
    : { grid: '#e2e8f0', tick: '#94a3b8', axis: '#64748b', guide: '#cbd5e1', dot: '#ffffff' }

  const [yLo, yHi] = useMemo(() => {
    const all = DEPLOYMENTS.flatMap((d) => series[d.key])
    return niceBounds(all)
  }, [series])

  const xAt = (i: number) => M.left + (i / (CONCURRENCY.length - 1)) * PLOT_W
  const yAt = (v: number) => M.top + PLOT_H - ((v - yLo) / (yHi - yLo)) * PLOT_H

  const gridLines = useMemo(() => {
    const steps = 5
    return Array.from({ length: steps + 1 }, (_, i) => ({
      v: Math.round(yLo + ((yHi - yLo) * i) / steps),
      y: M.top + PLOT_H - (i / steps) * PLOT_H,
    }))
  }, [yLo, yHi])

  function onMove(e: React.MouseEvent) {
    const svg = svgRef.current
    if (!svg) return
    const rect = svg.getBoundingClientRect()
    const vbX = ((e.clientX - rect.left) / rect.width) * VBW
    const idx = Math.round(((vbX - M.left) / PLOT_W) * (CONCURRENCY.length - 1))
    setHover(Math.max(0, Math.min(CONCURRENCY.length - 1, idx)))
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-sm font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Distributed &amp; Cloud Systems
            </div>
            <h1 className="mt-2 text-4xl font-semibold tracking-tight">
              Deployment Benchmark Dashboard
            </h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600 dark:text-slate-400">
              A four-service game backend deployed three ways on Google Cloud, load-tested to
              measure how deployment topology and sync vs async coupling trade off latency and
              throughput.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
              <div className="flex items-center gap-2">
                <Cloud className="h-4 w-4" />
                <span>GCE · e2-medium</span>
              </div>
            </div>
            <button
              onClick={() => setTheme(dark ? 'light' : 'dark')}
              aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
              className="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white p-3 text-slate-600 shadow-sm transition hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>
        </div>

        <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {SERVICES.map((s) => (
            <div
              key={s.name}
              className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-slate-500 dark:text-slate-400">{s.name}</div>
                  <span className="mt-2 inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
                    {s.role}
                  </span>
                  <div className="mt-2 text-sm text-slate-500 dark:text-slate-400">{s.desc}</div>
                </div>
                <div className="rounded-2xl bg-slate-100 p-3 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                  <s.icon className="h-6 w-6" />
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-6">
            <Panel
              title="Deployment benchmark"
              right={
                <span className="text-xs font-medium text-slate-400 dark:text-slate-500">
                  {meta.better === 'higher' ? 'higher is better' : 'lower is better'}
                </span>
              }
            >
              <div className="mb-4 flex flex-wrap items-center gap-x-6 gap-y-3">
                <Pills
                  value={coupling}
                  onChange={(v) => setCoupling(v as Coupling)}
                  options={[
                    { v: 'sync', label: 'Sync' },
                    { v: 'async', label: 'Async' },
                  ]}
                />
                <Pills
                  value={metric}
                  onChange={(v) => setMetric(v as Metric)}
                  options={[
                    { v: 'throughput', label: 'Throughput' },
                    { v: 'mean', label: 'Mean' },
                    { v: 'p95', label: 'P95' },
                    { v: 'p99', label: 'P99' },
                  ]}
                />
              </div>

              <div className="mb-3 flex flex-wrap items-center gap-x-5 gap-y-2">
                {DEPLOYMENTS.map((d) => (
                  <span key={d.key} className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
                    <svg width="22" height="8" aria-hidden>
                      <line
                        x1="0"
                        y1="4"
                        x2="22"
                        y2="4"
                        stroke={d.color}
                        strokeWidth="2.5"
                        strokeDasharray={d.dash === '0' ? undefined : d.dash}
                      />
                    </svg>
                    {d.name}
                  </span>
                ))}
              </div>

              <div className="relative">
                <svg
                  ref={svgRef}
                  viewBox={`0 0 ${VBW} ${VBH}`}
                  className="w-full"
                  role="img"
                  aria-label={`${meta.axis} versus concurrency for three deployments, ${coupling} coupling`}
                  onMouseMove={onMove}
                  onMouseLeave={() => setHover(null)}
                >
                  {gridLines.map((g, i) => (
                    <g key={i}>
                      <line x1={M.left} y1={g.y} x2={VBW - M.right} y2={g.y} stroke={C.grid} strokeWidth="1" />
                      <text x={M.left - 9} y={g.y + 4} textAnchor="end" fontSize="11" fill={C.tick}>
                        {g.v}
                      </text>
                    </g>
                  ))}

                  {CONCURRENCY.map((c, i) => (
                    <text key={c} x={xAt(i)} y={VBH - M.bottom + 22} textAnchor="middle" fontSize="11" fill={C.tick}>
                      {c}
                    </text>
                  ))}
                  <text x={M.left + PLOT_W / 2} y={VBH - 6} textAnchor="middle" fontSize="11" fill={C.axis}>
                    Concurrent requests (virtual users)
                  </text>
                  <text
                    x={-(M.top + PLOT_H / 2)}
                    y={14}
                    textAnchor="middle"
                    fontSize="11"
                    fill={C.axis}
                    transform="rotate(-90)"
                  >
                    {meta.axis}
                  </text>

                  {hover !== null && (
                    <line
                      x1={xAt(hover)}
                      y1={M.top}
                      x2={xAt(hover)}
                      y2={M.top + PLOT_H}
                      stroke={C.guide}
                      strokeWidth="1"
                      strokeDasharray="3 3"
                    />
                  )}

                  {DEPLOYMENTS.map((d) => (
                    <polyline
                      key={d.key}
                      points={series[d.key].map((v, i) => `${xAt(i)},${yAt(v)}`).join(' ')}
                      fill="none"
                      stroke={d.color}
                      strokeWidth="2.5"
                      strokeLinejoin="round"
                      strokeLinecap="round"
                      strokeDasharray={d.dash === '0' ? undefined : d.dash}
                    />
                  ))}

                  {DEPLOYMENTS.map((d) =>
                    series[d.key].map((v, i) => (
                      <circle
                        key={`${d.key}-${i}`}
                        cx={xAt(i)}
                        cy={yAt(v)}
                        r={hover === i ? 4.5 : 2.5}
                        fill={hover === i ? d.color : C.dot}
                        stroke={d.color}
                        strokeWidth="2"
                      />
                    )),
                  )}
                </svg>

                {hover !== null && (
                  <div
                    className="pointer-events-none absolute top-1 z-10 -translate-x-1/2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg dark:border-slate-700 dark:bg-slate-800"
                    style={{ left: `${(xAt(hover) / VBW) * 100}%` }}
                  >
                    <p className="mb-1 font-medium text-slate-500 dark:text-slate-400">{CONCURRENCY[hover]} VUs</p>
                    {DEPLOYMENTS.map((d) => (
                      <p key={d.key} className="flex items-center gap-2 whitespace-nowrap">
                        <span className="inline-block h-2 w-2 rounded-full" style={{ background: d.color }} />
                        <span className="text-slate-500 dark:text-slate-400">{d.name}</span>
                        <span className="ml-3 font-medium text-slate-900 dark:text-slate-100">
                          {series[d.key][hover]} {meta.unit}
                        </span>
                      </p>
                    ))}
                  </div>
                )}
              </div>

              <p className="mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                {takeaway(metric, coupling)}
              </p>
            </Panel>

            <Panel title="All results at 150 VUs">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 text-left text-slate-500 dark:border-slate-800 dark:text-slate-400">
                      <th className="pb-2 font-medium">Deployment</th>
                      <th className="pb-2 text-right font-medium">Throughput</th>
                      <th className="pb-2 text-right font-medium">Mean</th>
                      <th className="pb-2 text-right font-medium">P95</th>
                      <th className="pb-2 text-right font-medium">P99</th>
                    </tr>
                  </thead>
                  <tbody>
                    {DEPLOYMENTS.map((d) => {
                      const last = (m: Metric) => DATA[m][coupling][d.key][CONCURRENCY.length - 1]
                      return (
                        <tr key={d.key} className="border-b border-slate-50 last:border-0 dark:border-slate-800/70">
                          <td className="py-2.5">
                            <span className="flex items-center gap-2 font-medium text-slate-900 dark:text-slate-100">
                              <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: d.color }} />
                              {d.name}
                            </span>
                          </td>
                          <td className="py-2.5 text-right tabular-nums text-slate-700 dark:text-slate-300">{last('throughput')} ops/s</td>
                          <td className="py-2.5 text-right tabular-nums text-slate-700 dark:text-slate-300">{last('mean')} ms</td>
                          <td className="py-2.5 text-right tabular-nums text-slate-700 dark:text-slate-300">{last('p95')} ms</td>
                          <td className="py-2.5 text-right tabular-nums text-slate-700 dark:text-slate-300">{last('p99')} ms</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
              <p className="mt-3 text-xs text-slate-400 dark:text-slate-500">
                Showing the {coupling === 'sync' ? 'synchronous' : 'asynchronous'} run at peak concurrency.
                Toggle Sync / Async above to compare.
              </p>
            </Panel>
          </div>

          <div className="space-y-6">
            <Panel title={`${meta.label} at 150 VUs`}>
              <div className="grid grid-cols-1 gap-3">
                {DEPLOYMENTS.map((d) => (
                  <div key={d.key} className="rounded-2xl bg-slate-100 p-4 dark:bg-slate-800">
                    <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                      <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: d.color }} />
                      {d.name}
                    </div>
                    <div className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
                      {series[d.key][CONCURRENCY.length - 1]}
                      <span className="ml-1 text-sm font-normal text-slate-500 dark:text-slate-400">{meta.unit}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="Experiment setup">
              <div className="space-y-3">
                {SETUP.map((s) => (
                  <div key={s.label} className="flex items-start gap-3">
                    <div className="rounded-xl bg-slate-100 p-2 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                      <s.icon className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-slate-900 dark:text-slate-100">{s.label}</div>
                      <div className="text-sm text-slate-500 dark:text-slate-400">{s.value}</div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 rounded-2xl border border-transparent bg-slate-900 p-4 font-mono text-xs leading-relaxed text-slate-100 dark:border-slate-800 dark:bg-slate-950">
                <div className="text-slate-400">{'// sample run condition'}</div>
                <div>{'{'}</div>
                <div className="pl-3">"deployment": "multi-vm · cross-zone",</div>
                <div className="pl-3">"coupling": "{coupling}",</div>
                <div className="pl-3">"concurrency_vus": 50,</div>
                <div className="pl-3">"driver": "loadtest/bench.py"</div>
                <div>{'}'}</div>
              </div>
            </Panel>
          </div>
        </div>

        <footer className="mt-10 border-t border-slate-200 pt-5 text-xs leading-relaxed text-slate-400 dark:border-slate-800 dark:text-slate-500">
          <p>
            Comparing single-VM, multi-VM, and Kubernetes deployments under synchronous and
            asynchronous coupling — sync runs ≈ 80–190 ms end-to-end, async ≈ 20–60 ms.
          </p>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-flex items-center gap-1.5 text-slate-500 transition hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
          >
            <Github className="h-3.5 w-3.5" />
            github.com/HaoC916/Microservices-Game-Backend
          </a>
        </footer>
      </div>
    </div>
  )
}

function Panel({
  title,
  children,
  right,
}: {
  title: string
  children: React.ReactNode
  right?: React.ReactNode
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-6 py-4 dark:border-slate-800">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
        {right}
      </div>
      <div className="p-6">{children}</div>
    </div>
  )
}

function Pills({
  options,
  value,
  onChange,
}: {
  options: { v: string; label: string }[]
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => {
        const active = o.v === value
        return (
          <button
            key={o.v}
            onClick={() => onChange(o.v)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
              active
                ? 'border-slate-900 bg-slate-900 text-white dark:border-slate-100 dark:bg-slate-100 dark:text-slate-900'
                : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800'
            }`}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

export default App
