"""Tiny Python client for the RMTI API. Needs: pip install requests
    from rmti_client import RMTI
    api = RMTI("http://localhost:8000", api_key="YOUR_KEY")
    api.snapshot(domain="oncoclastics", site="breast", L=0.3, E=0.65, V=0.4, rho_now=0.2)
Research prototype. Send pseudonymous codes only, never names or identifiers."""
import requests


class RMTIError(Exception):
    def __init__(self, status, detail):
        super().__init__("HTTP %s: %s" % (status, detail))
        self.status, self.detail = status, detail


class RMTI:
    def __init__(self, base_url="http://localhost:8000", api_key=None, admin_key=None, timeout=30):
        self.base, self.timeout = base_url.rstrip("/"), timeout
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key
        if admin_key:
            self.headers["X-Admin-Key"] = admin_key

    def _call(self, method, path, body=None, params=None):
        r = requests.request(method, self.base + path, json=body, params=params, headers=self.headers, timeout=self.timeout)
        if not r.ok:
            try:
                detail = r.json().get("detail", r.text)
            except ValueError:
                detail = r.text
            raise RMTIError(r.status_code, detail)
        return r.json()

    def health(self): return self._call("GET", "/health")
    def snapshot(self, **f): return self._call("POST", "/v1/snapshot", f)
    def trajectory(self, **f): return self._call("POST", "/v1/trajectory", f)
    def cohort_rank(self, patients, domain="hcc", site=None): return self._call("POST", "/v1/cohort/rank", {"domain": domain, "site": site, "patients": patients})
    def validate(self, records, domain="hcc", site=None, bootstrap=0): return self._call("POST", "/v1/validate", {"domain": domain, "site": site, "records": records, "bootstrap": bootstrap})
    def lung_inputs(self, **f): return self._call("POST", "/v1/lung/inputs", f)
    def hcc_patient(self, **f): return self._call("POST", "/v1/hcc/patient", f)
    def two_sense(self, **f): return self._call("POST", "/v1/oncoclastics/two-sense", f)
    def two_sense_trajectory(self, **f): return self._call("POST", "/v1/oncoclastics/trajectory", f)
    def fhir_risk_assessment(self, **f): return self._call("POST", "/v1/fhir/risk-assessment", f)
    def registry(self): return self._call("GET", "/v1/registry")
    def registry_evidence(self, scope=None, include_supplementary=True): return self._call("GET", "/v1/registry/evidence", params={"scope": scope, "include_supplementary": include_supplementary})
    def registry_parameters(self): return self._call("GET", "/v1/registry/parameters")
    def registry_cohorts(self): return self._call("GET", "/v1/registry/cohorts")
    def propose(self, target, reason, author, payload=None): return self._call("POST", "/v1/registry/proposals", {"target": target, "reason": reason, "author": author, "payload": payload or {}})
