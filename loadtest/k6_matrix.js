import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:7351";
const VUS = Number.parseInt(__ENV.VUS || "10", 10);
const DURATION = __ENV.DURATION || "60s";

export const options = {
  scenarios: {
    matrix: {
      executor: "constant-vus",
      vus: VUS,
      duration: DURATION,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
  },
  summaryTrendStats: ["min", "avg", "med", "max", "p(95)", "p(99)"],
};

export default function () {
  const res = http.get(BASE_URL);

  check(res, {
    "status is 200 or 302": (r) => r.status === 200 || r.status === 302,
  });

  sleep(0.2);
}
