import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:7351";

export const options = {
  scenarios: {
    smoke: {
      executor: "constant-vus",
      vus: 10,
      duration: "60s",
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
