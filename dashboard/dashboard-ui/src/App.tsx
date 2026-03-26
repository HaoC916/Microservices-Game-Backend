import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Server,
  ShieldCheck,
  WifiOff,
  RefreshCw,
  Database,
  BarChart3,
  Clock3,
  AlertTriangle,
} from "lucide-react";

/**
 * ============================================================
 * CMPT 756 - Dashboard UI 
 * ============================================================
 *
 * It fetches data from backend dashboard-api:
 *   - GET /health
 *   - GET /metrics
 *   - GET /summary
 *
 * Current local backend URL:
 *   http://localhost:8100
 *
 * If deploy the backend elsewhere later, update API_BASE below.
 */

const API_BASE = "http://localhost:8100";
const REFRESH_INTERVAL_MS = 3000;

/**
 * ------------------------------------------------------------
 * Type definitions
 * ------------------------------------------------------------
 * These types describe the shape of the data returned by the API.
 */

type HealthResponse = {
  ok?: boolean;
  service?: string;
  mode?: string;
};

type MetricsValues = {
  online_players?: number;
  active_matches?: number;
  matchmaking_queue?: number;
  peak_online_players?: number;
  recent_telemetry_events?: number;
};

type MetricsResponse = {
  ok?: boolean;
  service?: string;
  mode?: string;
  admin_api_base_url?: string;
  metrics?: MetricsValues;
  note?: string;
};

type UpstreamItem = {
  ok?: boolean;
  url?: string;
  status_code?: number | null;
  latency_ms?: number;
  data?: any;
  error?: string;
};

type ExperimentMetrics = {
  telemetry_mode?: string;
  sample_count?: number;
  login_mean_ms?: number | null;
  login_p95_ms?: number | null;
  match_search_mean_ms?: number | null;
  match_search_p95_ms?: number | null;
  telemetry_sync_mean_ms?: number | null;
};

type ExperimentsResponse = {
  ok?: boolean;
  service?: string;
  experiment_metrics?: ExperimentMetrics;
};

type SummaryResponse = {
  ok?: boolean;
  service?: string;
  mode?: string;
  telemetry_mode?: string;
  upstreams?: {
    admin_health?: UpstreamItem;
    admin_config?: UpstreamItem;
    telemetry_health?: UpstreamItem;
    telemetry_recent?: UpstreamItem;
    telemetry_summary?: UpstreamItem;
    nakama_api?: UpstreamItem;
    //nakama_console?: UpstreamItem;
  };
};

/**
 * ------------------------------------------------------------
 * Small helper functions
 * ------------------------------------------------------------
 */

/**
 * Fetch JSON from dashboard-api.
 *
 * If the backend returns an HTTP error code such as 502,
 * fetch() itself still succeeds, so we still parse the JSON body.
 */
async function fetchJson(path: string) {
  const response = await fetch(`${API_BASE}${path}`);
  return response.json();
}

/**
 * Send a POST request with JSON body to dashboard-api.
 * 
 * The backend can use this for actions that change state (telemetry mode).
 * Useful for remote config or control.
 */
async function postJson(path: string, body: unknown) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  return response.json();
}

/**
 * Fetch all dashboard data at once.
 * Promise.all allows the browser to request all endpoints in parallel
 */
async function fetchDashboardData() {
  const [health, metrics, summary, experiments] = await Promise.all([
    fetchJson("/health"),
    fetchJson("/metrics"),
    fetchJson("/summary"),
    fetchJson("/experiments/summary"),
  ]);

  return { health, metrics, summary, experiments };
}

/**
 * Convert a boolean status into a small style label.
 */
function getStatusStyle(ok: boolean) {
  return ok
    ? "bg-emerald-100 text-emerald-700 border-emerald-200"
    : "bg-amber-100 text-amber-700 border-amber-200";
}

function getLatencyDisplay(ok: boolean, latencyMs?: number) {
  if (!ok) return "Unavailable";
  if (typeof latencyMs === "number") return `${latencyMs} ms`;
  return "Reachable";
}

/**
 * ------------------------------------------------------------
 * Reusable UI components
 * ------------------------------------------------------------
 */

function Panel({
  title,
  children,
  right,
}: {
  title: string;
  children: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-6 py-4">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        {right}
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

function StatusBadge({ ok }: { ok: boolean }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${getStatusStyle(ok)}`}
    >
      {ok ? "Healthy" : "Degraded"}
    </span>
  );
}

function IconBox({ children }: { children: React.ReactNode }) {
  return <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">{children}</div>;
}

function MetricCard({
  title,
  value,
  subtitle,
  icon,
}: {
  title: string;
  value: string | number;
  subtitle?: React.ReactNode;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm text-slate-500">{title}</div>
          <div className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">{value}</div>
          {subtitle ? <div className="mt-1 text-sm text-slate-500">{subtitle}</div> : null}
        </div>
        <IconBox>{icon}</IconBox>
      </div>
    </div>
  );
}

 /**
  * Small mode switcher used by the Admin Service card.
  * It lets the user switch telemetry forwarding mode at runtime.
  */
function ModeSelector({
    currentMode,
    disabled,
    onChange,
  }: {
    currentMode: string;
    disabled?: boolean;
    onChange: (mode: "off" | "sync" | "async") => void;
  }) {
  const modes: Array<"off" | "sync" | "async"> = ["off", "sync", "async"];

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {modes.map((mode) => {
        const active = currentMode === mode;
        return (
          <button
            key={mode}
            disabled={disabled}
            onClick={() => onChange(mode)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
              active
                ? "border-slate-900 bg-slate-900 text-white"
                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
          >
            {mode}
          </button>
        );
      })}
    </div>
  );
}

/**
* Simple box used for small metric displays inside a panel.
*/
function SimpleMetricBox({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl bg-slate-100 p-4">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-slate-900">{value}</div>
    </div>
  );
}

/**
* Small box used for experiment summary values.
*/
function ExperimentMetricBox({
  label,
  value,
  subtitle,
}: {
  label: string;
  value: string | number;
  subtitle?: string;
}) {
  return (
    <div className="rounded-2xl bg-slate-100 p-4">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-slate-900">{value}</div>
      {subtitle ? <div className="mt-1 text-xs text-slate-500">{subtitle}</div> : null}
    </div>
  );
}

function UpstreamRow({ name, item }: { name: string; item?: UpstreamItem }) {
  const ok = !!item?.ok;
  const status = item?.status_code ?? "-";
  const url = item?.url ?? "-";
  const error = item?.error || item?.data?.error;

  return (
    <div className="grid grid-cols-1 gap-3 rounded-2xl border border-slate-200 p-4 lg:grid-cols-[180px_100px_1fr]">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-slate-900">{name}</span>
        <StatusBadge ok={ok} />
      </div>

      <div className="text-sm text-slate-600">HTTP: {status}</div>

      <div className="min-w-0">
        <div className="truncate text-sm text-slate-500">{url}</div>
        {error ? <div className="mt-1 break-words text-sm text-red-600">{error}</div> : null}
      </div>
    </div>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="mb-6 rounded-3xl border border-red-200 bg-red-50 p-4 text-red-700 shadow-sm">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-5 w-5" />
        <span>{message}</span>
      </div>
    </div>
  );
}

/**
 * ------------------------------------------------------------
 * Main page component
 * ------------------------------------------------------------
 * This component only manages:
 *   - state
 *   - loading
 *   - errors
 *   - refresh behavior
 *   - top-level layout
 *
 * The detailed UI blocks are delegated to small components above.
 */

export default function DashboardPage() {
  // State for backend responses
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [experiments, setExperiments] = useState<ExperimentsResponse | null>(null);

  // State for UI behavior
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState("");
  const [changingMode, setChangingMode] = useState(false);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [resettingTelemetry, setResettingTelemetry] = useState(false);

  /**
   * Load all dashboard data from the backend.
   *
   * This function is reused by:
   *   - initial page load
   *   - auto-refresh timer
   *   - manual refresh button
   */
  const loadData = async () => {
    //setLoading(true);
    setError(null);

    try {
      const data = await fetchDashboardData();
      setHealth(data.health);
      setMetrics(data.metrics);
      setSummary(data.summary);
      setExperiments(data.experiments);
      setLastUpdated(new Date().toLocaleString());

      // Mark initial load as finished
      if (!hasLoadedOnce) {
        setHasLoadedOnce(true);
        setLoading(false);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to fetch dashboard data.");

      // If the very first load fails, stop loading state as well.
      if (!hasLoadedOnce) {
        setHasLoadedOnce(true);
        setLoading(false);
      }
    } 
  };

  /**
   * Handle telemetry reset action.
   * This is triggered by a button in the UI, and sends a POST request to dashboard-api,
   * which then proxies it to telemetry-api. After resetting, we reload the data to update the UI.
   */
  const handleTelemetryReset = async () => {
    setResettingTelemetry(true);
    setError(null);

    try {
      await postJson("/telemetry/reset", {});
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to reset telemetry.");
    } finally {
      setResettingTelemetry(false);
    }
  };

  /**
   * Load data once when the page starts,
   * then refresh automatically every (REFRESH_INTERVAL_MS).
   */
  useEffect(() => {
    loadData();

    const timer = setInterval(() => {
      loadData();
    }, REFRESH_INTERVAL_MS);

    return () => clearInterval(timer);
  }, []);

  /**
   * Change telemetry mode through dashboard-api,
   * which then proxies the request to admin-api.
   */
  const handleModeChange = async (mode: "off" | "sync" | "async") => {
    setChangingMode(true);

    try {
      await postJson("/telemetry/mode", { mode });
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to update telemetry mode.");
    } finally {
      setChangingMode(false);
    }
  };

  /**
   * Derived values make the JSX cleaner.
   * Instead of writing long optional chains everywhere,
   * we calculate the important values once here.
   */
  const derived = useMemo(() => {
    const metricValues = metrics?.metrics || {};
    const upstreams = summary?.upstreams || {};
    const experimentData = experiments?.experiment_metrics || {};
    // Read telemetry preview data from telemetry-api.
    const rawTelemetryPreview = upstreams.telemetry_recent?.data || { count: 0, events: [] };
    // Reverse the event order on the frontend ==> the newest events appear first.
    const reversedTelemetryPreview = {
      ...rawTelemetryPreview,
      events: Array.isArray(rawTelemetryPreview.events)
        ? [...rawTelemetryPreview.events].reverse()
        : [],
    };

    return {
      metricValues,
      upstreams,
      dashboardOnline: !!health?.ok,
      dashboardMode: health?.mode || "—",
      telemetryMode: summary?.telemetry_mode || "unknown",

      recentTelemetryCount: metricValues.recent_telemetry_events ?? 0,

      adminOk: !!upstreams.admin_health?.ok,
      telemetryHealthOk: !!upstreams.telemetry_health?.ok,
      nakamaApiOk: !!upstreams.nakama_api?.ok,

      // latency : dashboard-api to admin-api, telemetry-api, nakama-api
      adminHealthLatencyMs: upstreams.admin_health?.latency_ms,
      telemetryHealthLatencyMs: upstreams.telemetry_health?.latency_ms,
      nakamaApiLatencyMs: upstreams.nakama_api?.latency_ms,

      //nakamaConsoleOk: !!upstreams.nakama_console?.ok,
      //telemetryPreview: upstreams.telemetry_recent?.data || { count: 0, events: [] },
      telemetryPreview: reversedTelemetryPreview, // newest telemetry events appear first.
      
      // experimentMetrics are placeholders for potential future metrics.
      experimentMetrics: {
        telemetryMode: experimentData.telemetry_mode ?? summary?.telemetry_mode ?? "unknown",
        sampleCount: experimentData.sample_count ?? 0,
        loginMeanMs: experimentData.login_mean_ms ?? "—",
        loginP95Ms: experimentData.login_p95_ms ?? "—",
        matchSearchMeanMs: experimentData.match_search_mean_ms ?? "—",
        matchSearchP95Ms: experimentData.match_search_p95_ms ?? "—",
        telemetrySyncMeanMs: experimentData.telemetry_sync_mean_ms ?? "—",
      },
    };
  }, [health, metrics, summary, experiments]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-7xl px-6 py-8">
        {/* Page header */}
        <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-sm font-medium uppercase tracking-wide text-slate-500">CMPT 756 Project</div>
            <h1 className="mt-2 text-4xl font-semibold tracking-tight">Game Service Dashboard</h1>
            <p className="mt-2 max-w-2xl text-base text-slate-600">
              Monitoring page for dashboard-api, admin-api, telemetry-api, and Nakama.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
              <div className="flex items-center gap-2">
                <Clock3 className="h-4 w-4" />
                <span>Last updated: {lastUpdated || "—"}</span>
              </div>
            </div>

            <button
              onClick={loadData}
              className="inline-flex items-center rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-slate-800"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </button>
          </div>
        </div>

        {/* Error banner */}
        {error ? <ErrorBanner message={error} /> : null}

        {/* Top metrics row */}
        <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            title="Dashboard Service"
            value={loading ? "Loading" : derived.dashboardOnline ? "Online" : "Offline"}
            subtitle={`Mode: ${derived.dashboardMode}`}
            icon={<BarChart3 className="h-6 w-6" />}
          />

          <MetricCard
            title="Admin Service"
            value={getLatencyDisplay(derived.adminOk, derived.adminHealthLatencyMs)}
            subtitle={
              derived.adminOk ? (
                <div>
                  <div className="text-sm text-slate-500">Current mode: {derived.telemetryMode}</div>
                  <ModeSelector
                    currentMode={derived.telemetryMode}
                    disabled={changingMode}
                    onChange={handleModeChange}
                  />
                </div>
              ) : (
                "Mode unavailable"
              )
            }
            icon={derived.adminOk ? <ShieldCheck className="h-6 w-6" /> : <WifiOff className="h-6 w-6" />}
          /> 

          <MetricCard
            title="Telemetry Service"
            value={getLatencyDisplay(derived.telemetryHealthOk, derived.telemetryHealthLatencyMs)}   
            subtitle={
              <div>
                <div>Events: {derived.recentTelemetryCount}</div>
                <div className="mt-2">
                  <button
                    onClick={handleTelemetryReset}
                    disabled={resettingTelemetry}
                    className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {resettingTelemetry ? "Resetting..." : "Reset"}
                  </button>
                </div>
              </div>
            }
            icon={derived.telemetryHealthOk ? <ShieldCheck className="h-6 w-6" /> : <WifiOff className="h-6 w-6" />}
          />

          <MetricCard
            title="Nakama API"
            value={getLatencyDisplay(derived.nakamaApiOk, derived.nakamaApiLatencyMs)}
            subtitle={derived.nakamaApiOk ? "Reachable" : "Unavailable"}
            icon={derived.nakamaApiOk ? <Server className="h-6 w-6" /> : <WifiOff className="h-6 w-6" />}
          />
        </div>


        {/* Main content area */}
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          {/* Left Column */}
          <div className="space-y-6">
            <Panel title="Experiment Metrics">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <ExperimentMetricBox
                  label="Telemetry Mode"
                  value={derived.experimentMetrics.telemetryMode}
                  subtitle="Current forwarding mode"
                />
                <ExperimentMetricBox
                  label="Login Mean"
                  value={derived.experimentMetrics.loginMeanMs}
                  subtitle="End-to-end login latency"
                />
                <ExperimentMetricBox
                  label="Login P95"
                  value={derived.experimentMetrics.loginP95Ms}
                  subtitle="Tail latency"
                />
                <ExperimentMetricBox
                  label="Match Search Mean"
                  value={derived.experimentMetrics.matchSearchMeanMs}
                  subtitle="Matchmaking latency"
                />
                <ExperimentMetricBox
                  label="Match Search P95"
                  value={derived.experimentMetrics.matchSearchP95Ms}
                  subtitle="Tail latency"
                />
                <ExperimentMetricBox
                  label="Telemetry Sync Mean"
                  value={derived.experimentMetrics.telemetrySyncMeanMs}
                  subtitle="Critical-path telemetry overhead"
                />
              </div>
            </Panel>

            <Panel title="Upstream Status Summary" right={<StatusBadge ok={!!summary?.ok} />}>
              <div className="space-y-3">
                <UpstreamRow name="Admin Health" item={derived.upstreams.admin_health} />
                <UpstreamRow name="Admin Config" item={derived.upstreams.admin_config} />
                <UpstreamRow name="Telemetry Health" item={derived.upstreams.telemetry_health} />
                <UpstreamRow name="Telemetry Recent" item={derived.upstreams.telemetry_recent} />
                <UpstreamRow name="Telemetry Summary" item={derived.upstreams.telemetry_summary} />
                <UpstreamRow name="Nakama API" item={derived.upstreams.nakama_api} />
              </div>
            </Panel>
          </div>  

          {/* Right Column */}
          <div className="space-y-6">
            <Panel title="Gameplay Metrics">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <SimpleMetricBox label="Online Players" value={derived.metricValues.online_players ?? 0} />
                <SimpleMetricBox label="Active Matches" value={derived.metricValues.active_matches ?? 0} />
                <SimpleMetricBox label="Queue Depth" value={derived.metricValues.matchmaking_queue ?? 0} />
                <SimpleMetricBox label="Peak Online" value={derived.metricValues.peak_online_players ?? 0} />
              </div>
            </Panel>
            
            <Panel title="Events Preview (recent 10 events)">
              <div className="max-h-[420px] overflow-y-auto overflow-x-hidden rounded-2xl bg-slate-950 p-4 text-sm text-slate-100">
                <pre className="whitespace-pre-wrap break-words">
                  {JSON.stringify(derived.telemetryPreview, null, 2)}
                </pre>
              </div>
            </Panel>

            <Panel title="Service Notes">
              <div className="space-y-2 text-sm text-slate-600">
                <div className="flex items-start gap-2">
                  <Database className="mt-0.5 h-4 w-4" />
                  <span>
                    Current gameplay metrics are placeholders and can be replaced with real aggregates later.
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <Server className="mt-0.5 h-4 w-4" />
                  <span>
                    Summary may show a degraded state when Nakama API is not reachable on port 7350, or when admin-api / telemetry-api are unavailable.
                  </span>
                </div>
              </div>
            </Panel>
          </div>
        </div>
      </div>
    </div>
  );
}
