"""Numerical validation and consistency checks for a public statistical release."""
import csv
import json
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analysis.core import calculate,diagnostic,two_sided_normal,Z95


def read_csv(name):
    with (ROOT/name).open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))


class CoreChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=calculate()
        cls.inputs=json.loads((ROOT/"data/inputs.json").read_text())

    def test_normal_calibration_and_extreme_tail(self):
        self.assertEqual(two_sided_normal(0),1)
        self.assertAlmostEqual(two_sided_normal(Z95),.05,places=14)
        self.assertEqual(two_sided_normal(8),two_sided_normal(-8))
        self.assertGreater(two_sided_normal(12),0)
        from scipy.stats import norm
        for h in self.r["headlines"]:
            self.assertTrue(math.isclose(h["two_sided_p"],2*norm.sf(h["abs_z"]),rel_tol=1e-12))

    def test_lotto_combinatorics_and_event(self):
        c=self.r["lotto"]["combinations"]
        self.assertEqual(c,15380937)
        product=math.prod(range(33,40))//math.factorial(7)
        self.assertEqual(c,product)
        self.assertEqual(c*c,236573222997969)
        self.assertTrue(math.isclose(self.r["lotto"]["two_independent_p"],(1/c)**2,rel_tol=1e-14))
        self.assertGreater(self.r["lotto"]["double_over_sns_p"],1)
        self.assertLess(self.r["lotto"]["double_over_sns_p"],1.2)

    def test_source_totals_and_valid_vote_base(self):
        rik=self.inputs["rik"]
        self.assertEqual(sum(rik["national_votes"]),4374187)
        self.assertEqual(sum(rik["kosovo_votes"]),34791)
        self.assertEqual(sum(rik["overseas_votes"]),79283)
        self.assertEqual(self.r["matched_valid_votes"],4260113)
        self.assertAlmostEqual(sum(x["poll_percent"] for x in self.inputs["lists"]),97.5)
        self.assertEqual(len(rik["national_votes"]),len(self.inputs["lists"]))
        self.assertEqual(self.inputs["rik"]["status"],"provisional")

    def test_affine_invariance_requires_scaling_se(self):
        a=diagnostic(47.4,38.97,2.1)
        b=diagnostic(47.4/.975,38.97/.975,2.1/.975)
        self.assertTrue(math.isclose(a["two_sided_p"],b["two_sided_p"],rel_tol=1e-12))
        self.assertAlmostEqual(38.97-a["abs_z"]*a["se_pp"],30.54)

    def test_csv_inputs_match_json(self):
        rows=read_csv("data/headline.csv")
        self.assertEqual(len(rows),2)
        for row,h in zip(rows,self.r["headlines"]):
            self.assertEqual(float(row["estimate"]),h["estimate_percent"])
            self.assertEqual(float(row["benchmark"]),h["benchmark_percent"])
            self.assertEqual(float(row["margin"]),h["margin_95_pp"])
        votes=read_csv("data/rik_counts.csv")
        for i,row in enumerate(votes):
            for key in ["national_votes","kosovo_votes","overseas_votes"]:
                self.assertEqual(int(row[key]),self.inputs["rik"][key][i])

    def test_r_agrees_on_primary_geographic_and_historical_results(self):
        primary=read_csv("r_verification.csv")
        for rr,py in zip(primary,self.r["headlines"]):
            self.assertTrue(math.isclose(float(rr["p"]),py["two_sided_p"],rel_tol=1e-10))
        geo=read_csv("r_geography_verification.csv")
        for rr,py in zip(geo,self.r["geography_valid_vote_scenarios"]):
            self.assertTrue(math.isclose(float(rr["p"]),py["two_sided_p"],rel_tol=1e-10))
        old=read_csv("r_historical_verification.csv")
        for py in self.r["historical_2012"]["scenarios"]:
            rr=next(x for x in old if int(x["n"])==py["n_assumed"] and float(x["threshold"])==py["threshold"])
            self.assertTrue(math.isclose(float(rr["upper_tail"]),py["upper_tail"],rel_tol=1e-10))

    def test_binomial_tails_match_independent_library(self):
        from scipy.stats import binom
        prob=self.r["historical_2012"]["two_candidate_share"]
        for h in self.r["historical_2012"]["scenarios"]:
            expected=binom.sf(h["k"]-1,h["n_assumed"],prob)
            self.assertTrue(math.isclose(h["upper_tail"],expected,rel_tol=1e-10))

    def test_alternative_shapes_retain_same_95_interval(self):
        from analysis.shape_sensitivity import scenarios
        from scipy.stats import t
        for s in scenarios():
            self.assertAlmostEqual(2*t.sf(2.1/s["scale_pp"],s["df"]),.05,places=10)
            self.assertGreater(s["p"],self.r["headlines"][0]["two_sided_p"])

    def test_sensitivity_is_monotone(self):
        for h in self.r["headlines"]:
            probs=[x["two_sided_p"] for x in h["se_multipliers"]]
            self.assertEqual(probs,sorted(probs))
            self.assertAlmostEqual(two_sided_normal(h["abs_z"]/h["se_factor_to_reach_p_05"]),.05,places=12)


class PublicationChecks(unittest.TestCase):
    def test_executed_notebook_has_no_errors(self):
        import nbformat
        nb=nbformat.read(ROOT/"analiza.ipynb",as_version=4)
        nbformat.validate(nb)
        cells=[c for c in nb.cells if c.cell_type=="code"]
        self.assertGreaterEqual(len(cells),10)
        for c in cells:
            self.assertIsNotNone(c.execution_count)
            self.assertFalse(any(o.output_type=="error" for o in c.outputs))

    def test_local_html_links_and_no_external_dependencies(self):
        from bs4 import BeautifulSoup
        from urllib.parse import urlsplit,unquote
        for path in (ROOT/"docs").glob("*.html"):
            soup=BeautifulSoup(path.read_text(encoding="utf-8"),"html.parser")
            self.assertEqual(soup.html.get("lang"),"sr-Latn")
            self.assertFalse(soup.find_all("script"))
            for a in soup.find_all("a",href=True):
                url=urlsplit(a["href"])
                if url.scheme or url.netloc:continue
                target=path.parent/unquote(url.path) if url.path else path
                self.assertTrue(target.exists(),f"Broken link: {path.name}: {a['href']}")
                if url.fragment and target.suffix==".html":
                    dest=BeautifulSoup(target.read_text(encoding="utf-8"),"html.parser")
                    self.assertIsNotNone(dest.find(id=url.fragment),a["href"])
            for image in soup.find_all("img"):
                self.assertTrue(image.get("alt"))
                self.assertTrue(image.get("src","").startswith("data:image/"))
            self.assertIn("privremeni",soup.get_text().lower())

    def test_published_results_match_calculation(self):
        expected=calculate()
        self.assertEqual(json.loads((ROOT/"results.json").read_text()),expected)
        self.assertEqual(json.loads((ROOT/"docs/results.json").read_text()),expected)


if __name__=="__main__":unittest.main()
