export type Coupling = 'sync' | 'async'
export type Metric = 'throughput' | 'mean' | 'p95' | 'p99'
export type DeploymentKey = 'single' | 'multi' | 'k8s'

export const CONCURRENCY = [25, 50, 75, 100, 125, 150]

export type Deployment = {
  key: DeploymentKey
  name: string
  color: string
  dash: string
  blurb: string
}

export const DEPLOYMENTS: Deployment[] = [
  {
    key: 'single',
    name: 'Single-VM',
    color: '#3b82f6',
    dash: '0',
    blurb: 'All four services in Docker on one e2-medium VM (us-west1). Baseline.',
  },
  {
    key: 'multi',
    name: 'Multi-VM',
    color: '#f59e0b',
    dash: '7 4',
    blurb: 'Services split across VMs in four zones (us-west1/2, us-east1/4).',
  },
  {
    key: 'k8s',
    name: 'Kubernetes',
    color: '#10b981',
    dash: '2 4',
    blurb: 'GKE-managed pods with built-in load balancing.',
  },
]

export type MetricMeta = {
  label: string
  short: string
  unit: string
  better: 'higher' | 'lower'
  axis: string
}

export const METRICS: Record<Metric, MetricMeta> = {
  throughput: {
    label: 'Throughput',
    short: 'Throughput',
    unit: 'ops/s',
    better: 'higher',
    axis: 'Throughput (ops/s)',
  },
  mean: {
    label: 'Latency · mean',
    short: 'Mean',
    unit: 'ms',
    better: 'lower',
    axis: 'End-to-end latency (ms)',
  },
  p95: {
    label: 'Latency · p95',
    short: 'P95',
    unit: 'ms',
    better: 'lower',
    axis: 'End-to-end latency (ms)',
  },
  p99: {
    label: 'Latency · p99',
    short: 'P99',
    unit: 'ms',
    better: 'lower',
    axis: 'End-to-end latency (ms)',
  },
}

type Series = Record<DeploymentKey, number[]>

export const DATA: Record<Metric, Record<Coupling, Series>> = {
  throughput: {
    sync: {
      single: [34, 60, 71, 78, 74, 67],
      multi: [31, 53, 67, 77, 83, 80],
      k8s: [30, 56, 72, 86, 94, 100],
    },
    async: {
      single: [44, 80, 98, 108, 102, 92],
      multi: [38, 78, 99, 110, 118, 113],
      k8s: [40, 82, 104, 121, 131, 136],
    },
  },
  mean: {
    sync: {
      single: [80, 85, 90, 96, 103, 110],
      multi: [88, 95, 101, 108, 119, 130],
      k8s: [79, 83, 87, 91, 96, 100],
    },
    async: {
      single: [21, 23, 25, 27, 29, 31],
      multi: [23, 25, 28, 30, 33, 37],
      k8s: [20, 21, 23, 25, 26, 28],
    },
  },
  p95: {
    sync: {
      single: [90, 97, 104, 112, 122, 132],
      multi: [99, 107, 115, 124, 141, 158],
      k8s: [88, 93, 99, 104, 111, 118],
    },
    async: {
      single: [25, 27, 30, 32, 34, 38],
      multi: [28, 30, 33, 36, 42, 48],
      k8s: [24, 26, 28, 30, 32, 35],
    },
  },
  p99: {
    sync: {
      single: [101, 112, 126, 138, 148, 158],
      multi: [114, 128, 141, 152, 172, 190],
      k8s: [99, 107, 117, 123, 130, 136],
    },
    async: {
      single: [31, 34, 38, 41, 44, 48],
      multi: [34, 38, 43, 46, 53, 60],
      k8s: [29, 32, 35, 38, 40, 43],
    },
  },
}

export function takeaway(metric: Metric, coupling: Coupling): string {
  const band =
    coupling === 'sync'
      ? 'Synchronous coupling makes the client block on an admin gate before matchmaking, so end-to-end latency sits in the ~80–190 ms band.'
      : 'Asynchronous coupling skips the blocking gate, pulling end-to-end latency down to the ~20–60 ms band.'
  if (metric === 'throughput') {
    return `Kubernetes keeps scaling toward 150 VUs, the single VM peaks near 100 then saturates, and multi-VM tops out in between. Async sustains more throughput than sync at every load. ${band}`
  }
  return `Multi-VM carries the worst tail latency — extra cross-zone hops amplify delay — while Kubernetes stays lowest and flattest under load, and a single VM is competitive until it saturates. ${band}`
}
