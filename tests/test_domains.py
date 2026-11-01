"""The Disaster Science domain must not show medical vocabulary; the Greek rho must be accepted in file headers. Skips if streamlit is missing."""
import os, re, sys, unittest
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
try:
    from streamlit.testing.v1 import AppTest
except Exception:
    AppTest = None
MED = re.compile(r"patient|clinic|smok|oncolog|HCC|lung|FHIR|ECOG|surveillance|ethic|nurse|hepat|tumou?r|screening|biolog|care-system|histology|\bsex\b", re.I)


def _visible(at):
    out = []
    for kind in ("markdown", "caption", "info", "warning", "error", "subheader", "title", "text"):
        out += [str(e.value) for e in getattr(at, kind)]
    out += [str(m.label) for m in at.metric]
    for kind in ("slider", "number_input", "text_input", "selectbox", "radio", "button", "expander"):
        out += [str(getattr(e, "label", "")) for e in getattr(at, kind)]
    return [re.sub(r"\s+", " ", t) for t in out if t]


@unittest.skipUnless(AppTest, "streamlit not installed")
class DomainWording(unittest.TestCase):
    def _app(self, domain):
        at = AppTest.from_file(os.path.join(ROOT, "app.py.py"), default_timeout=90).run()
        at.sidebar.radio[0].set_value(domain).run()
        self.assertEqual([e.value for e in at.exception], [])
        return at

    def test_disaster_domain_has_no_medical_vocabulary(self):
        hits = [t[:100] for t in _visible(self._app("Disaster Science")) if MED.search(t)]
        self.assertEqual(hits, [])

    def test_disaster_validation_demo_uses_assets_not_patients(self):
        at = self._app("Disaster Science")
        self.assertIn("Assets / events", [m.label for m in at.metric])
        tables = " ".join(d.value.to_string() for d in at.dataframe)
        self.assertIn("coastal", tables)
        self.assertNotIn("smoker", tables)
        self.assertNotIn("S000", tables)

    def test_oncology_domain_keeps_its_clinical_wording(self):
        txt = " ".join(_visible(self._app("Oncoclastics (cancer)")))
        for w in ("patient", "Clinicians and nurses", "surveillance"):
            self.assertIn(w, txt)


class Headers(unittest.TestCase):
    def test_greek_rho_accepted_in_sandbox_headers(self):
        import sandbox as B
        o = B.run("breast", records=[dict(patient_id="a", L=0.3, V=0.4, **{"ρ": 0.25})])
        self.assertAlmostEqual(o["mean"]["rho"], 0.25)
        o = B.run("lung", records=[dict(patient_id="a", risk5=0.03, v_count=1, **{"ρ_care": 0.3})])
        self.assertAlmostEqual(o["mean"]["rho"], 0.3, places=6)

    def test_disaster_demo_file_validates_in_the_engine(self):
        import pandas as pd, service as S
        df = pd.read_csv(os.path.join(ROOT, "sample_data", "synthetic_disaster_serial.csv"))
        self.assertNotIn("smoker", " ".join(df["stratum"].unique()))
        v = S.validate_serial(df.rename(columns={"asset_id": "patient_id"}), "disaster")
        self.assertEqual((v["n"], v["events"]), (60, 12))


if __name__ == "__main__":
    unittest.main()
