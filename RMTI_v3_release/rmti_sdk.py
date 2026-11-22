"""Tiny Python SDK for the RMTI API.   pip install requests

    from rmti_sdk import RMTIClient
    c = RMTIClient("http://localhost:8000", "rmti_sandbox_demo")
    print(c.score(L=0.7, E=0.6, V=0.8, rho=0.35)["tier"])
"""
from __future__ import annotations

import time

import requests


class RMTIError(Exception):
    def __init__(self, status: int, code: str, detail: str, request_id: str | None = None):
        super().__init__(f"[{status} {code}] {detail} (request_id={request_id})")
        self.status, self.code, self.detail, self.request_id = status, code, detail, request_id


class RMTIClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0, max_retries: int = 3):
        self.base = base_url.rstrip("/")
        self.timeout, self.max_retries = timeout, max_retries
        self.http = requests.Session()
        self.http.headers.update({"X-API-Key": api_key, "User-Agent": "rmti-sdk/1.0"})

    def _call(self, method: str, path: str, json: dict | None = None):
        for attempt in range(self.max_retries + 1):
            r = self.http.request(method, self.base + path, json=json, timeout=self.timeout)
            if r.status_code == 429 and attempt < self.max_retries:
                time.sleep(min(float(r.headers.get("Retry-After", 1)), 30))
                continue
            if r.status_code >= 500 and attempt < self.max_retries:
                time.sleep(2 ** attempt * 0.5)
                continue
            if r.ok:
                return r.json()
            try:
                p = r.json()
            except ValueError:
                p = {}
            raise RMTIError(r.status_code, p.get("code", "http_error"),
                            p.get("detail", r.text[:200]), p.get("request_id"))

    def score(self, L, E, V, rho, site="general", label=None):
        return self._call("POST", "/v1/risk/score",
                          {"L": L, "E": E, "V": V, "rho": rho, "site": site, "label": label})

    def fhir(self, L, E, V, rho, site="general", label=None):
        return self._call("POST", "/v1/risk/score/fhir",
                          {"L": L, "E": E, "V": V, "rho": rho, "site": site, "label": label})

    def batch(self, items: list[dict]):
        return self._call("POST", "/v1/risk/batch", {"items": items})

    def sensitivity(self, lever, L, E, V, rho, steps=21):
        return self._call("POST", "/v1/risk/sensitivity",
                          {"lever": lever, "L": L, "E": E, "V": V, "rho": rho, "steps": steps})

    def usage(self):
        return self._call("GET", "/v1/usage")
