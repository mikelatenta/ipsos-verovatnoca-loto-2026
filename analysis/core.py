"""Conditional normal-model diagnostics; Python 3 standard library only.

No estimated probability of fabrication, intent, or total survey error.
All input figures live in data/inputs.json. Run: python analysis/core.py
"""
from pathlib import Path
from statistics import NormalDist
import csv
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "inputs.json"
Z95 = NormalDist().inv_cdf(0.975)


def two_sided_normal(z):
    """Numerically stable at extreme z; never subtract a CDF from 1."""
    return math.erfc(abs(z) / math.sqrt(2.0))


def diagnostic(estimate, benchmark, margin, se_multiplier=1.0):
    se = margin / Z95 * se_multiplier
    error = estimate - benchmark
    z = error / se
    p = two_sided_normal(z)
    return {"estimate_percent": estimate, "benchmark_percent": benchmark,
            "error_pp": error, "margin_95_pp": margin, "se_pp": se,
            "signed_z": z, "abs_z": abs(z), "two_sided_p": p,
            "one_sided_tail": p / 2, "one_in": 1 / p}


def binomial_upper(n, prob, threshold):
    """P(X >= ceil(n * threshold)), log-sum-exp; no normal approximation."""
    k = math.ceil(n * threshold - 1e-12)
    logs = [math.lgamma(n+1)-math.lgamma(j+1)-math.lgamma(n-j+1)
            + j*math.log(prob)+(n-j)*math.log1p(-prob) for j in range(k,n+1)]
    m = max(logs)
    tail = math.exp(m)*math.fsum(math.exp(v-m) for v in logs)
    return {"n_assumed": n, "threshold": threshold, "k": k, "upper_tail": tail}


def calculate():
    source = json.loads(INPUT.read_text(encoding="utf-8"))
    headlines = []
    for row in source["lists"]:
        if "rik_display_percent" not in row:
            continue
        margin = (row["ci_high"]-row["ci_low"])/2
        result = diagnostic(row["poll_percent"], row["rik_display_percent"], margin)
        result.update({"number":row["number"], "list":row["short"]})
        result["se_multipliers"] = [dict(multiplier=k, **diagnostic(
            row["poll_percent"], row["rik_display_percent"], margin, k))
            for k in [1,1.5,2,3,4]]
        # A scenario on the *reported margin*, not a confidence interval for p.
        result["rounded_margin_sensitivity"] = [diagnostic(
            row["poll_percent"], row["rik_display_percent"], m) for m in [2.05,2.10,2.15]]
        result["variance_equivalent_n"] = (row["poll_percent"]/100)*(1-row["poll_percent"]/100)/(result["se_pp"]/100)**2
        result["se_factor_to_reach_p_05"] = abs(result["error_pp"])/margin
        headlines.append(result)
    rik = source["rik"]
    national = rik["national_votes"]
    matched = [a-b-c for a,b,c in zip(national,rik["kosovo_votes"],rik["overseas_votes"])]
    valid_factor = 1-source["poll"]["invalid_assumption_percent"]/100
    geography = []
    for h in headlines:
        i = h["number"]-1
        geography.append(dict(list=h["list"], national_valid_percent=100*national[i]/sum(national),
            matched_votes=matched[i], **diagnostic(h["estimate_percent"]/valid_factor,
                100*matched[i]/sum(matched), h["margin_95_pp"]/valid_factor)))
    combinations = math.comb(source["lotto"]["pool"],source["lotto"]["draw"])
    lotto_one = 1/combinations
    lotto_two = 1/combinations**2
    lotto = {"combinations": combinations, "single_p":lotto_one,
             "two_independent_p":lotto_two, "two_independent_one_in":combinations**2,
             "single_over_sns_p":lotto_one/headlines[0]["two_sided_p"],
             "double_over_sns_p":lotto_two/headlines[0]["two_sided_p"]}
    old = source["historical_2012"]
    p2012 = old["tadic_votes"]/(old["tadic_votes"]+old["nikolic_votes"])
    history = {"two_candidate_share": p2012,
        "error_pp": old["tadic_poll_percent"]-100*p2012,
        "scenarios":[binomial_upper(n,p2012,t) for n in [1198,655,300] for t in [.58,.575]]}
    return {"version":source["version"], "input_sha256":hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "interpretation":"Conditional normal-model diagnostics, not an identified probability for the actual survey or its intent.",
        "z_975":Z95,"headlines":headlines,"lotto":lotto,
        "matched_valid_votes":sum(matched),"national_valid_votes":sum(national),
        "geography_valid_vote_scenarios":geography,"historical_2012":history}


def export(result):
    (ROOT/"results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    inp = json.loads(INPUT.read_text(encoding="utf-8"))
    with (ROOT/"data"/"headline.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.writer(f); writer.writerow(["list","estimate","benchmark","margin"])
        for h in result["headlines"]:
            writer.writerow([h["list"],h["estimate_percent"],h["benchmark_percent"],h["margin_95_pp"]])
    with (ROOT/"data"/"rik_counts.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.writer(f); writer.writerow(["number","list","poll_percent","national_votes","kosovo_votes","overseas_votes"])
        for i,row in enumerate(inp["lists"]):
            writer.writerow([i+1,row["short"],row["poll_percent"],*[inp["rik"][key][i] for key in ["national_votes","kosovo_votes","overseas_votes"]]])


if __name__ == "__main__":
    r = calculate(); export(r)
    for h in r["headlines"]:
        print(f'{h["list"]}: z={h["signed_z"]:.12g}, p={h["two_sided_p"]:.12g}, 1/p={h["one_in"]:.12g}')
    print("Loto 7/39:",r["lotto"])
