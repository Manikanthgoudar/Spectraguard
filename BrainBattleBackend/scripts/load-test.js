import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 100, // 100 Virtual Users
  duration: '1m', // 1 Minute continuous load
  thresholds: {
    http_req_failed: ['rate<0.05'], // < 5% failure rate
    http_req_duration: ['p(95)<1500'], // 95% of requests < 1.5s
  },
};

export default function () {
  const url = __ENV.BACKEND_URL || 'http://127.0.0.1:8000/health';
  const res = http.get(url);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  
  sleep(0.1);
}
