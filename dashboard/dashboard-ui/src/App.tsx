import { useMemo, useRef, useState } from 'react'
import { Github, Server, Network, GitBranch, Activity } from 'lucide-react'
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

const VBW = 760
const VBH = 380
const M = { top: 24, right: 20, bottom: 46, left: 56 }
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
  const [coupling, setCoupling] = useState<Coupling>('sync')
  const [metric, setMetric] = useState<Metric>('throughput')
  const [hover, setHover] = useState<number | null>(null)
  const svgRef = useRef<SVGSVGElement | null>(null)

  const meta = METRICS[metric]
  const series = DATA[metric][coupling]

  const [yLo, yHi] = useMemo(() => {
    const all = DEPLOYMENTS.flatMap((d) => series[d.key])
    return niceBounds(all)
  }, [series])

  const xAt = (i: number) => M.left + (i / (CONCURRENCY.length - 1)) * PLOT_W
  const yAt = (v: number) => M.top + PLOT_H - ((v - yLo) / (yHi - yLo)) * PLOT_H

  const gridLines = useMemo(() => {
    const steps = 5
    return Array.from({ length: steps + 1 }, (_, i) => {
      const v = yLo + ((yHi - yLo) * i) / steps
      return { v: Math.round(v), y: M.top + PLOT_H - (i / steps) * PLOT_H }
    })
  }, [yLo, yHi])

  function onMove(e: React.MouseEvent) {
    const svg = svgRef.current
    if (!svg) return
    const rect = svg.getBoundingClientRect()
    const vbX = ((e.clientX - rect.left) / rect.width) * VBW
    const t = (vbX - M.left) / PLOT_W
    const idx = Math.round(t * (CONCURRENCY.length - 1))
    setHover(Math.max(0, Math.min(CONCURRENCY.length - 1, idx)))
  }

  const facts = [
    { icon: Server, label: '4 services', sub: 'Nakama · Admin · EventHub · Dashboard' },
    { icon: Network, label: '3 deployments', sub: 'Single-VM · Multi-VM · Kubernetes' },
    { icon: GitBranch, label: 'Sync vs async', sub: 'gate-on vs gate-off coupling' },
    { icon: Activity, label: '25 → 150 VUs', sub: 'concurrency sweep on GCE' },
  ]

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 antialiased">
      <div className="mx-auto max-w-4xl px-5 py-10 sm:py-14">
        <header className="mb-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-widest text-sky-400/80">
                Cloud deployment benchmark
              </p>
              <h1 className="mt-1 text-2xl font-semibold text-white sm:text-3xl">
                Microservices game backend
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
                A four-service game-ops backend deployed three ways on Google Cloud, then
                load-tested to see what each deployment choice costs in latency and throughput.
              </p>
            </div>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noreferrer"
              className="hidden shrink-0 items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 transition hover:border-slate-500 hover:text-white sm:inline-flex"
            >
              <Github size={16} />
              Code
            </a>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {facts.map((f) => (
              <div
                key={f.label}
                className="rounded-xl border border-slate-800 bg-slate-900/60 p-3"
              >
                <f.icon size={16} className="text-slate-500" />
                <p className="mt-2 text-sm font-medium text-slate-100">{f.label}</p>
                <p className="mt-0.5 text-[11px] leading-snug text-slate-500">{f.sub}</p>
              </div>
            ))}
          </div>
        </header>

        <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-slate-500">
              Coupling
            </p>
            <Segmented
              options={[
                { v: 'sync', label: 'Sync' },
                { v: 'async', label: 'Async' },
              ]}
              value={coupling}
              onChange={(v) => setCoupling(v as Coupling)}
            />
          </div>
          <div>
            <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-slate-500">
              Metric
            </p>
            <Segmented
              options={[
                { v: 'throughput', label: 'Throughput' },
                { v: 'mean', label: 'Mean' },
                { v: 'p95', label: 'P95' },
                { v: 'p99', label: 'P99' },
              ]}
              value={metric}
              onChange={(v) => setMetric(v as Metric)}
            />
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 sm:p-5">
          <div className="mb-3 flex flex-wrap items-center gap-x-5 gap-y-2">
            {DEPLOYMENTS.map((d) => (
              <span key={d.key} className="flex items-center gap-2 text-xs text-slate-400">
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
            <span className="ml-auto text-[11px] text-slate-500">
              {meta.better === 'higher' ? 'higher is better' : 'lower is better'}
            </span>
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
                  <line
                    x1={M.left}
                    y1={g.y}
                    x2={VBW - M.right}
                    y2={g.y}
                    stroke="#1e293b"
                    strokeWidth="1"
                  />
                  <text x={M.left - 10} y={g.y + 4} textAnchor="end" fontSize="11" fill="#64748b">
                    {g.v}
                  </text>
                </g>
              ))}

              {CONCURRENCY.map((c, i) => (
                <text
                  key={c}
                  x={xAt(i)}
                  y={VBH - M.bottom + 22}
                  textAnchor="middle"
                  fontSize="11"
                  fill="#64748b"
                >
                  {c}
                </text>
              ))}
              <text
                x={M.left + PLOT_W / 2}
                y={VBH - 6}
                textAnchor="middle"
                fontSize="11"
                fill="#94a3b8"
              >
                Concurrent requests (virtual users)
              </text>
              <text
                x={-(M.top + PLOT_H / 2)}
                y={15}
                textAnchor="middle"
                fontSize="11"
                fill="#94a3b8"
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
                  stroke="#475569"
                  strokeWidth="1"
                  strokeDasharray="3 3"
                />
              )}

              {DEPLOYMENTS.map((d) => {
                const pts = series[d.key].map((v, i) => `${xAt(i)},${yAt(v)}`).join(' ')
                return (
                  <polyline
                    key={d.key}
                    points={pts}
                    fill="none"
                    stroke={d.color}
                    strokeWidth="2.5"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                    strokeDasharray={d.dash === '0' ? undefined : d.dash}
                  />
                )
              })}

              {DEPLOYMENTS.map((d) =>
                series[d.key].map((v, i) => (
                  <circle
                    key={`${d.key}-${i}`}
                    cx={xAt(i)}
                    cy={yAt(v)}
                    r={hover === i ? 4.5 : 2.5}
                    fill={hover === i ? d.color : '#0f172a'}
                    stroke={d.color}
                    strokeWidth="2"
                  />
                )),
              )}
            </svg>

            {hover !== null && (
              <div
                className="pointer-events-none absolute top-1 z-10 -translate-x-1/2 rounded-lg border border-slate-700 bg-slate-950/95 px-3 py-2 text-xs shadow-xl"
                style={{ left: `${(xAt(hover) / VBW) * 100}%` }}
              >
                <p className="mb-1 font-medium text-slate-400">{CONCURRENCY[hover]} VUs</p>
                {DEPLOYMENTS.map((d) => (
                  <p key={d.key} className="flex items-center gap-2 whitespace-nowrap">
                    <span
                      className="inline-block h-2 w-2 rounded-full"
                      style={{ background: d.color }}
                    />
                    <span className="text-slate-400">{d.name}</span>
                    <span className="ml-auto font-medium text-slate-100">
                      {series[d.key][hover]} {meta.unit}
                    </span>
                  </p>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-3">
          {DEPLOYMENTS.map((d) => {
            const last = series[d.key][CONCURRENCY.length - 1]
            return (
              <div key={d.key} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-sm"
                    style={{ background: d.color }}
                  />
                  <span className="text-xs text-slate-400">{d.name}</span>
                </div>
                <p className="mt-2 text-2xl font-semibold text-white">
                  {last}
                  <span className="ml-1 text-xs font-normal text-slate-500">{meta.unit}</span>
                </p>
                <p className="text-[11px] text-slate-500">at 150 VUs</p>
              </div>
            )
          })}
        </div>

        <p className="mt-5 text-sm leading-relaxed text-slate-400">{takeaway(metric, coupling)}</p>

        <footer className="mt-10 border-t border-slate-800 pt-5 text-[11px] leading-relaxed text-slate-600">
          <p>
            CMPT 756 · Distributed &amp; Cloud Systems. Values reconstructed from the study's
            result figures (sync ≈ 80–190 ms, async ≈ 20–60 ms end-to-end) to illustrate the
            deployment trade-offs.
          </p>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-flex items-center gap-1.5 text-slate-400 transition hover:text-white"
          >
            <Github size={13} />
            github.com/HaoC916/Microservices-Game-Backend
          </a>
        </footer>
      </div>
    </div>
  )
}

function Segmented({
  options,
  value,
  onChange,
}: {
  options: { v: string; label: string }[]
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div className="inline-flex overflow-hidden rounded-lg border border-slate-700">
      {options.map((o, i) => {
        const on = o.v === value
        return (
          <button
            key={o.v}
            onClick={() => onChange(o.v)}
            className={[
              'px-3.5 py-1.5 text-sm transition',
              i > 0 ? 'border-l border-slate-700' : '',
              on
                ? 'bg-slate-200 font-medium text-slate-900'
                : 'bg-transparent text-slate-400 hover:text-slate-100',
            ].join(' ')}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

export default App
