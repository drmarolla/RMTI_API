import os
import pytest
pytest.importorskip("streamlit"); pytest.importorskip("geopandas"); pytest.importorskip("folium")
from streamlit.testing.v1 import AppTest

APP = os.path.join(os.path.dirname(__file__), "..", "streamlit_app.py")


def test_app_runs_and_presets_reproduce_paper():
    at = AppTest.from_file(APP, default_timeout=180).run()
    assert not at.exception
    at.sidebar.selectbox[0].select("Urban · Lagos").run()
    m = {x.label: x.value for x in at.metric}
    assert (m["R now"], m["R after"], m["Risk reduction"]) == ("0.374", "0.211", "43.8%")


def test_app_buttons_and_oncology_tab():
    at = AppTest.from_file(APP, default_timeout=180).run()
    for b in at.button:
        b.click().run(timeout=180)
    assert not at.exception
    at.tabs[4].radio[0].set_value("District access & surveillance map").run(timeout=180)
    assert not at.exception


def test_app_sar_demo():
    at = AppTest.from_file(APP, default_timeout=180).run()
    at.tabs[3].radio[0].set_value("Synthetic demo (SAR pre/post)").run(timeout=180)
    for b in at.tabs[3].button:
        if b.label == "Run demo":
            b.click().run(timeout=180)
    assert not at.exception
    assert any(m.label == "E_sel (assets in hazard)" for m in at.metric)
