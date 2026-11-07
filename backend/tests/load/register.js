import http from "k6/http";
import { check } from "k6";

const runId = Date.now();

export const options = {
  scenarios: {
    register: {
      executor: "per-vu-iterations",
      vus: Number(__ENV.USERS || 100),
      iterations: 1,
      maxDuration: "2m",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    checks: ["rate>0.99"],
  },
};

export default function () {
  const response = http.post(
    `${__ENV.BASE_URL || "http://localhost:8000"}/auth/register`,
    JSON.stringify({
      email: `loadtest-${runId}-${__VU}@example.com`,
      password: "LoadTest-password-123!",
    }),
    {
      headers: { "Content-Type": "application/json" },
      timeout: "60s",
    },
  );

  check(response, {
    "registration returns 201": (r) => r.status === 201,
  });
}
