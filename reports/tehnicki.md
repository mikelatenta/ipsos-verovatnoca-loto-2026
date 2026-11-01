# Tehnička analiza: objavljena margina, normalni repovi i Loto

**Mihajlo Popesku · verzija 1.0.0 · 01.11.2026.**

Ovo je izvršeni Python notebook, sa ulazima, formulama, kodom, rezultatima i proverama. Osnovna analiza je marginalni normalni model za dve liste. Ne predstavljamo ga kao identifikovan model stvarnog Ipsosovog postupka. Ne izvodimo verovatnoću namere, prevare ili nameštanja.

**Referenca:** zamrznut privremeni RIK presek 30.10.2026. 09:10; nije konačan rezultat. Svi prikazani brojevi potiču iz `data/inputs.json`.

## 1. Pokretanje i ulazni podaci

Za osnovni račun dovoljan je Python 3.11+ bez dodatnih biblioteka. Ceo notebook i grafikoni koriste biblioteke navedene u `requirements.txt`. Pokretanje: `python analysis/core.py`; puna izrada: `python build.py`. Iz korena repozitorijuma pokrenuti i `Rscript analysis/verify.R` za nezavisnu proveru.

```python
from pathlib import Path
import sys, json, math
root = Path.cwd()
if not (root / "data" / "inputs.json").exists():
    root = root.parent
sys.path.insert(0, str(root))
from analysis.core import calculate, two_sided_normal, diagnostic, binomial_upper, Z95
from analysis.shape_sensitivity import scenarios
from IPython.display import display, Markdown, Image
inputs = json.loads((root / "data" / "inputs.json").read_text(encoding="utf-8"))
r = calculate()
print("Python:", sys.version.split()[0])
print("SHA-256 ulaza:", r["input_sha256"])
print("Ukupni uzorak:", inputs["poll"]["total_n"])
print("Broj opredeljenih:", inputs["poll"]["decided_n"])
print("RIK presek:", inputs["rik"]["snapshot_displayed_local"])
```

Objavljene procene dve glavne liste su 47,40% i 40,00%, a granice intervala 45,3–49,5% i 37,9–42,1%. Poluširina oba intervala je 2,10 procentnih poena. RIK referentni procenti su 38,97% i 53,03%.

U ukupnih 3.624 ulaze i osobe koje nisu navele listu. Nije objavljena relevantna neponderisana baza opredeljenih, varijansa nakon ponderisanja, dizajn-efekat niti model spajanja telefonskog i onlajn uzorka. Iz margine se može izvesti *varijansno ekvivalentna* veličina jednostavnog slučajnog uzorka, ali to nije rekonstrukcija stvarnog broja opredeljenih. Ni 95% interval sam ne identifikuje raspodelu greške van tog intervala.

## 2. Model i događaj koji računamo

Udeo izražavamo u procentnim poenima. Za izabranu referencu θ pretpostavljamo procenu Q sa raspodelom `Normal(θ, SE²)`, gde je `SE = m / Φ⁻¹(0,975)`, a `m` objavljena poluširina 95% intervala. Referentni RIK udeo tretira se kao fiksiran: ova analiza ne proverava integritet izbornog brojanja.

Za opaženu razliku `d = q − θ` računamo `z = d/SE` i **dvostrani događaj** `|Q − θ| ≥ |d|`. Verovatnoća u tom modelu je `p = 2 Φ(−|z|) = erfc(|z|/√2)`. Ovo nije verovatnoća tačno jedne vrednosti, niti posteriorna verovatnoća hipoteze.

Numerički koristimo `erfc`, bez nestabilnog izraza `1 − Φ(z)`, koji za velike z može vratiti nulu zbog zaokruživanja u računaru. Numerički precizan normalni rep i opravdanost normalnog modela dva su odvojena pitanja.

```python
for h in r["headlines"]:
    print(h["list"])
    for key in ["error_pp", "margin_95_pp", "se_pp", "signed_z", "two_sided_p", "one_in", "variance_equivalent_n"]:
        print(f"  {key}: {h[key]:.15g}")
```

| Lista | Ipsos | RIK* | Razlika (pp) | &#124;z&#124; | Dvostrano p, normalni model |
| --- | --- | --- | --- | --- | --- |
| SNS / Ujedinjena Srbija | 47,40% | 38,97% | 8,43 | 7,868 | 3,608 × 10<sup>−15</sup> |
| Studentska lista | 40,00% | 53,03% | -13,03 | 12,161 | 5,007 × 10<sup>−34</sup> |

*RIK: privremeni objavljeni procenti u sačuvanom preseku. Negativan znak razlike za Studentsku listu znači potcenjivanje.

Za SNS dobijamo oko 1 u 277,2 biliona, zaokruženo 280 biliona. Rezultat za Studentsku listu prikazan je odvojeno. **Te dve verovatnoće ne množimo:** udeli lista iz iste ankete zavise jedan od drugog. Ovo nije zajednički test svih lista, a prikaz je naknadna dijagnostika, ne unapred registrovan test.

```python
display(Image(filename=str(root / "docs/assets/02-normalna-dve-ose.png")))
```

## 3. Loto 7/39: precizna definicija poređenja

Pretpostavljamo ravnopravne kombinacije. Jedna kombinacija je neuređen skup od sedam različitih brojeva među 39, pa je broj mogućnosti `C(39,7)`. Za jednu unapred izabranu kombinaciju u jednom izvlačenju, `p₁ = 1/C(39,7)`. Za po jednu kombinaciju u dva unapred određena nezavisna izvlačenja, `p₂ = p₁²`.

Ne računamo dve pobede bilo kada, sve igrače zajedno, veliki broj listića, sisteme ili dodatne igre. Kombinacije ne moraju biti iste u oba izvlačenja; bitno je da je po jedna izabrana pre svakog relevantnog nezavisnog izvlačenja.

```python
combinations = math.comb(39, 7)
p_single = 1 / combinations
p_double = p_single ** 2
p_sns = r["headlines"][0]["two_sided_p"]
print("Broj kombinacija:", combinations)
print("Jedna sedmica:", p_single)
print("Dve sedmice:", p_double)
print("Jednom u:", combinations ** 2)
print("Jedna sedmica / SNS p:", p_single / p_sns)
print("Dve sedmice / SNS p:", p_double / p_sns)
```

Dve sedmice imaju verovatnoću 4,227 × 10<sup>−15</sup>; to je oko 1,172 puta verovatnije od SNS događaja u normalnom modelu. Poređenje se odnosi na veličinu dva broja. Ne čini modele ekvivalentnim niti opravdava pretpostavke ankete.

```python
display(Image(filename=str(root / "docs/assets/03-loto-poredjenje.png")))
```

## 4. Osetljivost na širinu greške

Ako je stvarna standardna greška `k` puta veća od izvedene, tada je novi z jednak `z/k`. Množilac standardne greške nije isto što i dizajn-efekat na varijansu: `DEFF = k²` u ovom pojednostavljenom poređenju. Scenariji nisu procene stvarnog DEFF-a. Oni ne ispravljaju sistematsku pristrasnost, već menjaju samo rasipanje oko nepromenjenog centra.

```python
for h in r["headlines"]:
    print(h["list"])
    for s in h["se_multipliers"]:
        print(f'  k={s["multiplier"]:3g}: z={s["abs_z"]:.6f}; p={s["two_sided_p"]:.12g}')
    print("  k potreban za p=0.05:", h["se_factor_to_reach_p_05"])
```

| Množilac SE | SNS: p | Studentska: p |
| --- | --- | --- |
| 1,0 | 3,608 × 10<sup>−15</sup> | 5,007 × 10<sup>−34</sup> |
| 1,5 | 1,561 × 10<sup>−7</sup> | 5,171 × 10<sup>−16</sup> |
| 2,0 | 8,357 × 10<sup>−5</sup> | 1,198 × 10<sup>−9</sup> |
| 3,0 | 8,726 × 10<sup>−3</sup> | 5,041 × 10<sup>−5</sup> |
| 4,0 | 4,919 × 10<sup>−2</sup> | 2,364 × 10<sup>−3</sup> |

Za SNS, k ≈ 4,014 dovodi odstupanje do granice centralnih 95%; za Studentsku listu k ≈ 6,205. To ne dokazuje da su stvarne greške toliko velike.

```python
display(Image(filename=str(root / "docs/assets/04-osetljivost.png")))
```

### Zaokruživanje objavljene margine

Preciznost ulaza ne opravdava mnogo značajnih cifara u javnoj tvrdnji. Kao jednostavnu proveru menjamo marginu od 2,05 do 2,15 pp, uz fiksirane objavljene procente. Ovo je scenario zaokruživanja margine, ne puna zajednička optimizacija svih zaokruženih procenata i krajeva intervala, i ne interval pouzdanosti za p.

```python
for item in r["headlines"][0]["rounded_margin_sensitivity"]:
    print(f'margina={item["margin_95_pp"]:.2f}; p={item["two_sided_p"]:.12g}; 1/p={item["one_in"]:.12g}')
```

## 5. Isti 95% interval ne znači iste repove

Normalnost je dodatna pretpostavka. Kao matematički kontraprimer uzimamo simetrične Studentove t-raspodele sa 5, 10 i 30 stepeni slobode i skaliramo svaku tako da njen **centralni 95% interval takođe bude ±2,10 pp**. Za t-raspodelu skala nije standardna devijacija. Ove raspodele nisu fitovane na Ipsosove podatke i ne tvrdimo da opisuju njegov uzorak.

Njihovi repovi pokazuju zašto 95% interval sam ne identifikuje verovatnoću na 7,87 normalnih standardnih grešaka. Studentova t-raspodela ovde nema veze sa nazivom Studentske liste.

```python
for s in scenarios():
    print(f't(df={s["df"]}): skala={s["scale_pp"]:.9g} pp; dvostrano p={s["p"]:.12g}')
print("Normalni model:", r["headlines"][0]["two_sided_p"])
```

| Model sa istim centralnim 95% intervalom | SNS: dvostrano p |
| --- | --- |
| Student t, df=5 | 1,470 × 10<sup>−4</sup> |
| Student t, df=10 | 4,375 × 10<sup>−6</sup> |
| Student t, df=30 | 3,759 × 10<sup>−9</sup> |
| Normalni | 3,608 × 10<sup>−15</sup> |

Ova provera ograničava tumačenje glavnog broja: vrlo mali normalni rep ne može bez dodatnih dokaza postati stvarna verovatnoća događaja u anketi.

## 6. Obuhvat birača i važeći glasovi

Ipsos isključuje Kosovo i Metohiju i građane koji žive u inostranstvu, dok nacionalni RIK presek obuhvata i te rezultate. Pored toga, Ipsos u objavljene udele ugrađuje pretpostavljenih 2,5% nevažećih listića. **Ne treba tvrditi da je Ipsos objavio samo važeće glasove:** njegovih 18 udela sabira se do 97,5%. Nacionalni RIK procenti takođe obuhvataju nevažeće u osnovici; broj izašlih birača nije nužno jednak broju listića u kutijama. Ne rekonstruišemo imenitelj prosto deljenjem brojem izašlih.

Za transparentnu dodatnu proveru koristimo same brojeve glasova za 18 lista: oduzmemo glasove na Kosovu i u inostranstvu, pa izračunamo udele među preostalim **važećim** glasovima. Ipsosove procente delimo sa 0,975. Ako istu normalnu pretpostavku prenosimo na novu skalu, **i standardnu grešku delimo sa 0,975**. To je uslovna transformacija sa fiksiranim faktorom, ne nova procena varijanse.

Oduzimanje regionalnih glasova približava geografsku osnovu; ne garantuje identičnu populaciju ispitanika, biračkih spiskova i onih koji su glasali, niti usklađuje trenutak merenja.

```python
print("Važeći glasovi, nacionalno:", r["national_valid_votes"])
print("Važeći glasovi, bez KiM i inostranstva:", r["matched_valid_votes"])
for g in r["geography_valid_vote_scenarios"]:
    print(g["list"])
    for key in ["estimate_percent", "benchmark_percent", "error_pp", "se_pp", "abs_z", "two_sided_p"]:
        print(f"  {key}: {g[key]:.12g}")
```

| Lista | Ipsos, važeći % | RIK, približen obuhvat i važeći % | Razlika pp | Uslovno normalno p |
| --- | --- | --- | --- | --- |
| SNS / Ujedinjena Srbija | 48,6154 | 39,4621 | 9,1533 | 8,131 × 10<sup>−17</sup> |
| Studentska lista | 41,0256 | 53,6293 | -12,6036 | 1,886 × 10<sup>−30</sup> |

Ova korekcija ne uklanja veliku razliku. Ipak, primarni broj 1 u 280 biliona ostaje jasno označen kao račun iz objavljenih procenata, a ne rezultat ove dodatne transformacije.

## 7. Istorijski dodatak: predsednički izbori 2012.

[Tanjugova vest preneta na B92, 11.05.2012.](https://www.b92.net/o/info/izbori2012/vesti?nav_id=608340) navodi Ipsosovih 58% za Borisa Tadića i 42% za Tomislava Nikolića, na ukupnom uzorku 1.198, sa istraživanjem 10. maja. Drugi krug održan je 20. maja, dakle deset dana kasnije. [Publikacija RZS/RIK](https://arhiva.rik.parlament.gov.rs/doc/arhiva/predsednik/2012/5.%202012%20publikacija%20rzs.compressed.pdf) daje 1.481.952 i 1.552.063 glasa (štampana strana 80, 84. stranica PDF-a).

Na osnovici glasova za dva kandidata, Tadić ima 48,84458%, pa je razlika oko 9,1554 pp. Nemamo originalnu metodološku dokumentaciju, objavljenu marginu ili stvarni broj opredeljenih. Zato ne primenjujemo marginu iz 2026. niti govorimo da smo izračunali stvarnu verovatnoću te ankete.

Sledi samo ilustracija: `X ~ Binomial(n, p₀)`, gde je p₀ konačni udeo glasova za Tadića među dva kandidata. Računamo `P(X ≥ ceil(nq))`. Prikazujemo hipotetička n = 1.198, 655 i 300; n = 655 nije utvrđen uzorak opredeljenih, već scenario. Pragovi su q = 0,58 i q = 0,575; drugi dopušta donji rub zaokruživanja na 58% na ceo procenat.

```python
print("Referentni udeo za Tadića:", r["historical_2012"]["two_candidate_share"])
for h in r["historical_2012"]["scenarios"]:
    print(f'n={h["n_assumed"]}; prag={h["threshold"]}; k={h["k"]}; gornji rep={h["upper_tail"]:.12g}')
```

Ovo su **jednostrani binomni repovi**, sa drugačijim modelom od glavnog dvostranog normalnog računa za 2026. Ne množimo ove verovatnoće sa onima za 2026, ne tretiramo dva odabrana slučaja kao reprezentativan uzorak rada agencije i iz njih ne izvodimo zaključak o nameri. Promene tokom deset dana, izlaznost i nepoznata relevantna baza posebno ograničavaju istorijsko poređenje.

## 8. Računske provere i šta bi omogućilo potpunu reviziju

Glavni normalni rep proverava se pomoću Python `math.erfc`, SciPy `norm.sf` i nezavisnog R `pnorm`. Istorijska binomna suma proverava se sa SciPy `binom.sf` i R `pbinom`. Testovi obuhvataju izvorne zbirove glasova, transformaciju osnovice i kombinatorni račun za Loto. Pokretanje: `python -m unittest discover -s tests -v`.

Računsko slaganje potvrđuje implementaciju zadatog modela. Ne potvrđuje da pretpostavke važe za stvarnu anketu. Za reviziju su potrebni relevantni brojevi ispitanika po modu i izbornoj opredeljenosti, upitnik, postupak izbora i regrutovanja, odziv, ponderi, model izlaznosti, postupanje sa neodlučnima i način izvođenja intervala. Anonimizovani podaci i dokumentacija omogućili bi proveru, uz zaštitu ispitanika.

Ne zaključujemo o profesionalnom ili pravnom prekršaju samo iz p-vrednosti. Ne tvrdimo da su kasne promene ili drugi izvori greške isključeni. Zajednički multinomni test nije predmet ove analize.

```python
from scipy.stats import norm, binom
for h in r["headlines"]:
    other = 2*norm.sf(h["abs_z"])
    assert math.isclose(other, h["two_sided_p"], rel_tol=1e-12)
for h in r["historical_2012"]["scenarios"]:
    other = binom.sf(h["k"]-1,h["n_assumed"],r["historical_2012"]["two_candidate_share"])
    assert math.isclose(other,h["upper_tail"],rel_tol=1e-10)
print("Nezavisne SciPy provere: sve prošle.")
```

## Izvori i poreklo podataka

1. **Ipsos Strategic Marketing**, [saopštenje od 22.10.2026.](https://www.ipsos.com/sr-rs/rezultati-istrazivanja-pred-parlamentarne-izbore-oktobar-2026): procene i 95% intervali, terenski rad 20–22.10, ukupno 3.624 ispitanika, 90% telefonskih i 10% onlajn intervjua. Broj opredeljenih nije objavljen. Naručilac naveden u saopštenju je lista Aleksandar Vučić – Ujedinjena Srbija.
2. **RIK**, [portal rezultata](https://www.rik.parlament.gov.rs/542645/rezultati/): ovde je zamrznut privremeni nacionalni presek **30.10.2026. u 09:10**, sa 8.339 od 8.392 obrađena biračka mesta. Regionalni brojevi sačuvani su 30.10.2026. To nisu konačni rezultati. [Ulazi u JSON formatu](https://github.com/mikelatenta/ipsos-verovatnoca-loto-2026/blob/main/data/inputs.json), [brojevi glasova](https://github.com/mikelatenta/ipsos-verovatnoca-loto-2026/blob/main/data/rik_counts.csv) i [poreklo podataka](https://github.com/mikelatenta/ipsos-verovatnoca-loto-2026/blob/main/data/PROVENANCE.md) omogućavaju proveru.
3. **Državna lutrija Srbije**, [uputstvo za Loto 7/39](https://lutrija.rs/Help/Instructions?helpTypeId=1) i [pravila igara](https://lutrija.rs/help/rules): izbor sedam brojeva od 39. Broj kombinacija i verovatnoće u ovoj analizi računaju se nezavisno, kombinatorno.
4. **AAPOR**, [standardi objavljivanja metodologije](https://aapor.org/standards-and-ethics/disclosure-standards/): izvor za potrebu objavljivanja uzorka, ponderisanja, načina prikupljanja i pretpostavki procene preciznosti.
5. **Mihajlo Popesku**, [objašnjenje objavljeno na X-u 31.10.2026.](https://x.com/visokodrustvo/status/2116459194765246791). Ovaj paket razvija isti normalni račun, dodaje poređenje sa Lotom, kod i provere osetljivosti.
6. **Goran S. Milovanović**, [referentni repozitorijum](https://github.com/GoranMilovanovic/izboriRepublikaSrbija_20261025): uzor za organizaciju javnog sažetka, tehničkog izveštaja i koda. Naš glavni račun ostaje marginalni normalni model izveden iz objavljene margine. Njegov multinomni test je drugačiji postupak; njegove rezultate ovde ne preuzimamo.

Verzija **1.0.0**, objavljena 01.11.2026. Autor: **Mihajlo Popesku**. Nove podatke treba uneti kao novu, jasno datiranu verziju; današnji živi portal ne treba poistovećivati sa sačuvanim presekom.

## Dodatak: izvorni kod osnovnog računa

Ispod je ceo modul `analysis/core.py`. Isti modul se koristi za tabele, rezultate i grafikone. Kod iz ovog dodatka čita se u kontekstu datoteke; notebook ga uvozi u prvom izvršnom koraku.

```python
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

```