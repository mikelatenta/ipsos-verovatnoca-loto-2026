"""Build all public documents from one set of inputs and execute the notebook.

Run from the repository root: python build.py
The R verification is required for release: Rscript analysis/verify.R
"""
from pathlib import Path
import base64
import csv
import hashlib
import html
import inspect
import json
import math
import os
import platform
import shutil
import sys

ROOT=Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/".matplotlib"))
os.environ.setdefault("JUPYTER_RUNTIME_DIR",str(ROOT/".jupyter"))
os.environ.setdefault("IPYTHONDIR",str(ROOT/".jupyter"/"ipython"))
os.environ.setdefault("XDG_CACHE_HOME",str(ROOT/".cache"))
for dirname in [".jupyter", ".jupyter/ipython", ".cache", ".matplotlib"]:
    (ROOT/dirname).mkdir(parents=True,exist_ok=True)
import markdown
import nbformat
from nbclient import NotebookClient
from analysis import core
from analysis.figures import generate
from analysis.shape_sensitivity import scenarios

REPO="https://github.com/mikelatenta/ipsos-verovatnoca-loto-2026"
SITE="https://mikelatenta.github.io/ipsos-verovatnoca-loto-2026/"
REF="https://github.com/GoranMilovanovic/izboriRepublikaSrbija_20261025"
POST="https://x.com/visokodrustvo/status/2116459194765246791"
DOCS=ROOT/"docs"
RESULT=core.calculate()
INP=json.loads(core.INPUT.read_text(encoding="utf-8"))
SNS,SL=RESULT["headlines"]
LOT=RESULT["lotto"]


def sr(value,d=2):
    return f"{value:,.{d}f}".replace(",","_").replace(".",",").replace("_",".")


def sci(value,d=3):
    exponent=math.floor(math.log10(value)); mantissa=value/(10**exponent)
    return f"{sr(mantissa,d)} × 10<sup>{str(exponent).replace('-', '−')}</sup>"


def table(headers,rows):
    def cell(value):
        return str(value).replace("|", "&#124;")
    return "| "+" | ".join(map(cell,headers))+" |\n| "+" | ".join(["---"]*len(headers))+" |\n"+"\n".join("| "+" | ".join(map(cell,row))+" |" for row in rows)+"\n"


def image(name,alt):
    return f"![{alt}](assets/{name}.png)"


def primary_table():
    return table(["Lista","Ipsos","RIK*","Razlika (pp)","|z|","Dvostrano p, normalni model"],
        [[h["list"],sr(h["estimate_percent"])+"%",sr(h["benchmark_percent"])+"%",sr(h["error_pp"]),
          sr(h["abs_z"],3),sci(h["two_sided_p"])] for h in RESULT["headlines"]])


def source_section():
    return f"""## Izvori i poreklo podataka

1. **Ipsos Strategic Marketing**, [saopštenje od 22.10.2026.]({INP['poll']['source']}): procene i 95% intervali, terenski rad 20–22.10, ukupno 3.624 ispitanika, 90% telefonskih i 10% onlajn intervjua. Broj opredeljenih nije objavljen. Naručilac naveden u saopštenju je lista Aleksandar Vučić – Ujedinjena Srbija.
2. **RIK**, [portal rezultata]({INP['rik']['source']}): ovde je zamrznut privremeni nacionalni presek **30.10.2026. u 09:10**, sa 8.339 od 8.392 obrađena biračka mesta. Regionalni brojevi sačuvani su 30.10.2026. To nisu konačni rezultati. [Ulazi u JSON formatu]({REPO}/blob/main/data/inputs.json), [brojevi glasova]({REPO}/blob/main/data/rik_counts.csv) i [poreklo podataka]({REPO}/blob/main/data/PROVENANCE.md) omogućavaju proveru.
3. **Državna lutrija Srbije**, [uputstvo za Loto 7/39](https://lutrija.rs/Help/Instructions?helpTypeId=1) i [pravila igara](https://lutrija.rs/help/rules): izbor sedam brojeva od 39. Broj kombinacija i verovatnoće u ovoj analizi računaju se nezavisno, kombinatorno.
4. **AAPOR**, [standardi objavljivanja metodologije](https://aapor.org/standards-and-ethics/disclosure-standards/): izvor za potrebu objavljivanja uzorka, ponderisanja, načina prikupljanja i pretpostavki procene preciznosti.
5. **Mihajlo Popesku**, [objašnjenje objavljeno na X-u 31.10.2026.]({POST}). Ovaj paket razvija isti normalni račun, dodaje poređenje sa Lotom, kod i provere osetljivosti.
6. **Goran S. Milovanović**, [referentni repozitorijum]({REF}): uzor za organizaciju javnog sažetka, tehničkog izveštaja i koda. Naš glavni račun ostaje marginalni normalni model izveden iz objavljene margine. Njegov multinomni test je drugačiji postupak; njegove rezultate ovde ne preuzimamo.

Verzija **1.0.0**, objavljena 01.11.2026. Autor: **Mihajlo Popesku**. Nove podatke treba uneti kao novu, jasno datiranu verziju; današnji živi portal ne treba poistovećivati sa sačuvanim presekom.
"""


def summary():
    return f"""<div class="eyebrow">SAŽETAK ZA JAVNOST · MIHAJLO POPESKU · 01.11.2026.</div>

# Šta znači „1 u 280 biliona“?

<p class="lead">Ipsosova procena, rezultat RIK-a i poređenje sa Lotom 7/39. Objašnjenje koje može da se pročita, proveri i ponovi.</p>

<div class="callout"><strong>Šta računamo:</strong> koliko bi, u normalnom modelu sa objavljenom preciznošću, bilo retko odstupanje za SNS od najmanje 8,43 procentna poena u bilo kom smeru. Ovo nije utvrđena verovatnoća greške stvarne ankete niti verovatnoća nameštanja.</div>

## Prvo podaci, pa verovatnoća

Ipsos je 22. oktobra 2026. objavio **47,40% za SNS / Ujedinjenu Srbiju** i **40,00% za Studentsku listu**, uz 95% interval od ±2,10 procentnih poena za svaku. U korišćenom privremenom preseku RIK-a od 30. oktobra, udeli su **38,97%** i **53,03%**. Razlike su **+8,43** i **−13,03 procentna poena**.

{image('01-procena-i-rezultat','Ipsosova procena i interval, uz referentni privremeni rezultat RIK-a za dve liste.')}

Anketa i izbori nisu merenje u istom trenutku, a obuhvat birača se razlikuje. Zato je potrebno jasno reći pod kojim pretpostavkama se poređenje pretvara u verovatnoću.

## Račun za SNS u tri koraka

1. Iz objavljene margine dobijamo standardnu grešku: **2,10 ÷ 1,96 ≈ 1,071 procentni poen**.
2. Razliku delimo tom greškom: **(47,40 − 38,97) ÷ 1,071 ≈ 7,87**. Toliko je standardnih grešaka procena udaljena od reference.
3. Sabiramo oba krajnja repa normalne raspodele: **p ≈ {sci(SNS['two_sided_p'],1)}**. Recipročna vrednost je oko **1 u {sr(SNS['one_in']/1e12,1)} biliona**, zaokruženo **1 u 280 biliona**.

{image('02-normalna-dve-ose','Normalna raspodela, RIK na 38,97 odsto, Ipsos na plus 7,87 standardnih grešaka, simetrična vrednost 30,54 odsto i dva uvećana repa.')}

Na gornjoj osi su procenti, a na donjoj standardne greške. **Nula znači odsustvo odstupanja od RIK-a**, a ne nula glasova. Leva vrednost 30,54% je zamišljeni, simetrični prag. Ne predstavlja rezultat drugog istraživanja.

## Poređenje sa Lotom

U Lotu 7/39 postoji **{sr(LOT['combinations'],0)}** kombinacija. Ako odigramo jednu kombinaciju, šansa za sedmicu u jednom izvlačenju iznosi 1 prema tom broju. Za dve sedmice, sa po jednom kombinacijom u **dva unapred određena, nezavisna izvlačenja**, verovatnoće se množe.

{table(['Događaj','Verovatnoća','Otprilike jednom u'],[
['Jedna loto sedmica',sci(LOT['single_p'],2),sr(LOT['combinations'],0)],
['Dve loto sedmice u dva određena izvlačenja',sci(LOT['two_independent_p'],2),sr(LOT['two_independent_one_in']/1e12,1)+' biliona'],
['SNS: jednako veliko ili veće odstupanje, normalni model',sci(SNS['two_sided_p'],2),sr(SNS['one_in']/1e12,1)+' biliona']])}

{image('03-loto-poredjenje','Logaritamsko poređenje jedne loto sedmice, dve sedmice i uslovne normalne verovatnoće za SNS.')}

**Brojevi su istog reda veličine.** Dve sedmice su oko **{sr(LOT['double_over_sns_p'],2)} puta verovatnije** od događaja za SNS u izabranom normalnom modelu. Jedna sedmica je oko **{sr(LOT['single_over_sns_p']/1e6,1)} miliona puta verovatnija**. Ovo nije tvrdnja da je anketa isto što i izvlačenje loptica: poređenje samo približava veličinu broja. Ne odnosi se na dve sedmice „bilo kada u životu“ niti na mnogo odigranih kombinacija.

## Gde su granice zaključka?

Račun pretpostavlja nepristrasno merenje istog biračkog tela, nepromenjenu podršku od ankete do izbora, ispravnu objavljenu preciznost i **normalnu raspodelu greške, uključujući njene krajnje repove**. Sam interval od 95% nije dovoljan da se ti repovi utvrde. U tehničkom delu pokazujemo koliko se broj menja ako promenimo širinu ili oblik raspodele.

Slučajna greška uzorka ne obuhvata sve što može da pomeri prognozu: neodaziv, izbor i ponderisanje ispitanika, model izlaznosti, postupanje sa neodlučnima, promenu mišljenja i druge izvore pristrasnosti. Bez tih podataka **ne možemo broj „1 u 280 biliona“ proglasiti stvarnom učestalošću ovakve greške Ipsosove ankete**.

Naš zaključak je precizan: **opažena razlika izuzetno je udaljena od onoga što očekuje izabrani normalni model sa objavljenom marginom**. Uzrok razlike zahteva proveru metodologije i podataka. Mali p sam po sebi ne utvrđuje nameru.

## Čitajte dalje ili proverite račun

- [Statistika 101: od uzorka do repova](statistika-101.html) — objašnjenje bez prethodnog znanja statistike.
- [Tehnički izveštaj i Python notebook](tehnicki.html) — pretpostavke, formule, izvršeni kod, tabele, osetljivost i istorijski dodatak za 2012.
- [Nezavisna računska provera u R-u](provera-r.html) — isti ulazni podaci, drugi softver.
- [Preuzmi izvršeni notebook](analiza.ipynb), [rezultate u JSON-u](results.json) ili [otvori GitHub repozitorijum]({REPO}).

{source_section()}
"""


def primer():
    return f"""<div class="eyebrow">STATISTIKA 101 · OBJAŠNJENJE UZ GRAFIK</div>

# Od uzorka do „1 u 280 biliona“

Anketa pokušava da na osnovu odgovora manjeg broja ljudi proceni šta misli mnogo veća grupa. Umesto da pitamo sve birače, pitamo uzorak. Ako je uzorak pravilno izabran i istraživanje dobro sprovedeno, njegovi odgovori mogu prilično dobro da opišu biračko telo.

## Zašto se uzorci razlikuju?

Kada bismo istog dana, na isti način, ispitali mnogo različitih slučajnih uzoraka, ne bismo svaki put dobili isti procenat. To kolebanje zovemo **slučajna greška uzorkovanja**. Veći uzorak ga obično smanjuje. U jednostavnom slučajnom uzorkovanju, približno četiri puta veći uzorak prepolovljava standardnu grešku. Ali veliki uzorak ne uklanja sistematsko izostavljanje određenih birača, neodaziv ili pristrasne odgovore.

**Procenat i procentni poen nisu isto.** Razlika između 47,40% i 38,97% je 8,43 procentna poena. To nije relativno povećanje od 8,43%.

## Šta je standardna greška?

Ona opisuje koliko procene variraju od uzorka do uzorka. Za običan, nezavisan slučajni uzorak i binarni odgovor približna formula je `SE = √[p(1−p)/n]`, gde je `p` udeo između 0 i 1, a `n` broj relevantnih ispitanika. Ponderi, grupisanje i način izbora uzorka menjaju ovu jednostavnu sliku.

Ovde **ne ubacujemo ukupnih 3.624 ispitanika u tu formulu**. Udeli lista računati su među opredeljenima, čiji broj nije objavljen, a dizajn i ponderi nisu dovoljno opisani da bismo rekonstruisali varijansu. Umesto toga, prihvatamo objavljenu marginu kao polaznu pretpostavku.

## Šta znači 95%?

U normalnom modelu, srednjih 95% procena nalazi se unutar približno 1,96 standardnih grešaka od centra. Ako je postupak nepristrasan i interval pravilno izračunat, dugoročno bi oko 95% tako konstruisanih intervala obuhvatilo fiksnu stvarnu vrednost. To nije garancija da izborni rezultat mora pasti u interval: podrška i sastav onih koji izađu mogu se promeniti.

Za objavljenu marginu od ±2,10 procentnih poena dobijamo:

<div class="formula">SE = 2,10 ÷ 1,9599639845 ≈ 1,071448 procentnih poena</div>

## Koliko je daleko Ipsosova procena?

RIK-ovih 38,97% koristimo kao referencu, odnosno centar modela. Ipsosovih 47,40% udaljeno je 8,43 procentna poena. Da bismo tu udaljenost izrazili u standardnim greškama, delimo:

<div class="formula">z = (47,40 − 38,97) ÷ 1,071448 ≈ 7,867855</div>

To je oko 7,87 standardnih grešaka. Na grafikonu nula na donjoj osi znači da nema odstupanja od RIK-a. Na gornjoj osi, na istom mestu, stoji 38,97%. Desni prag je 47,40%, a levi, simetrični prag je **38,97 − 8,43 = 30,54%**.

{image('02-normalna-dve-ose','Dve povezane horizontalne ose: procenti i standardne greške, uz uvećane repove normalne raspodele.')}

## Kako iz krive dobijamo verovatnoću?

Normalna raspodela ima oblik zvona. Mala odstupanja blizu centra su česta, veoma velika su retka. Ukupna površina ispod krive je 1, odnosno 100%. Površina u nekom delu krive predstavlja verovatnoću da rezultat upadne u taj deo.

Pitamo za **jednako veliko ili veće odstupanje u bilo kom smeru**. Zato sabiramo površinu levo od −7,867855 i desno od +7,867855. U normalnoj raspodeli te dve površine su jednake. Računar ih izračunava pomoću standardne matematičke funkcije; ne broji 280 biliona simulacija.

<div class="formula">p = P(Z ≤ −7,867855) + P(Z ≥ 7,867855)<br>p ≈ {sci(SNS['two_sided_p'],3)}</div>

Svaki rep daje polovinu tog broja. Ako bismo unapred pitali samo za precenjivanje, koristili bismo desni rep i dobili polovinu dvostrane verovatnoće. Ovde dosledno koristimo oba smera.

## Zašto „jedan u 280 biliona“?

Zapis „jedan u N“ dobija se kao `N = 1/p`. U našem računu to je približno **{sr(SNS['one_in'],0)}**, odnosno **277,2 biliona**, zaokruženo na **280 biliona**. Bilion ovde znači milion miliona, 10<sup>12</sup>.

U zamišljenom velikom broju ponavljanja istog modela, takav ili veći promašaj očekivali bismo prosečno jednom na toliko ponavljanja. To ne znači da bi se pojavio po rasporedu. Niti računamo verovatnoću da se ispiše baš broj 47,40%: računamo sve rezultate najmanje toliko udaljene od reference.

## Kako se računa Loto?

Redosled izvučenih brojeva nije važan. Broj različitih grupa od sedam brojeva iz skupa od 39 je:

<div class="formula">C(39,7) = 39! ÷ (7! × 32!) = {sr(LOT['combinations'],0)}</div>

Uz ravnopravne kombinacije, jedna od njih je naša, pa je šansa za sedmicu `1 / {LOT['combinations']}`. Za dve unapred određene nezavisne runde, sa po jednom kombinacijom u svakoj, računamo `1 / {LOT['combinations']}²`. Dobijamo **1 u {sr(LOT['two_independent_one_in'],0)}**, odnosno oko **236,6 biliona**. Zato je poređenje sa dve sedmice približno, a ne identično.

{image('03-loto-poredjenje','Poređenje verovatnoće jedne i dve loto sedmice sa uslovnim normalnim računom za SNS.')}

## Koje pretpostavke nose zaključak?

Za Loto polazimo od ravnopravnih kombinacija i nezavisnih izvlačenja. Za anketu su pretpostavke zahtevnije: isti ciljni birači i podrška, bez pristrasnosti, tačna objavljena standardna greška i normalni repovi. **Iz jednog 95% intervala ne možemo dokazati oblik krajnjih repova.** Druga raspodela može imati isti središnji interval i znatno veće krajnje verovatnoće.

Zato broj objašnjava određeni statistički model. Ne određuje verovatnoću nameštanja i sam ne razdvaja metodološku grešku, promenu podrške, izlaznost, neodaziv ili pogrešno izveštavanje. [Tehnički izveštaj](tehnicki.html) pokazuje i kako se račun menja kada promenimo pretpostavke.

Ovo je proširena i računski proverljiva verzija [autorove objave na X-u]({POST}). Podaci: Ipsos, 22.10.2026; privremeni RIK presek 30.10.2026. u 09:10. [Svi izvori](index.html#izvori-i-poreklo-podataka).
"""


def technical_cells():
    cells=[]
    def md(s): cells.append(nbformat.v4.new_markdown_cell(s.strip()))
    def code(s): cells.append(nbformat.v4.new_code_cell(s.strip()))
    md("""# Tehnička analiza: objavljena margina, normalni repovi i Loto

**Mihajlo Popesku · verzija 1.0.0 · 01.11.2026.**

Ovo je izvršeni Python notebook, sa ulazima, formulama, kodom, rezultatima i proverama. Osnovna analiza je marginalni normalni model za dve liste. Ne predstavljamo ga kao identifikovan model stvarnog Ipsosovog postupka. Ne izvodimo verovatnoću namere, prevare ili nameštanja.

**Referenca:** zamrznut privremeni RIK presek 30.10.2026. 09:10; nije konačan rezultat. Svi prikazani brojevi potiču iz `data/inputs.json`.

## 1. Pokretanje i ulazni podaci

Za osnovni račun dovoljan je Python 3.11+ bez dodatnih biblioteka. Ceo notebook i grafikoni koriste biblioteke navedene u `requirements.txt`. Pokretanje: `python analysis/core.py`; puna izrada: `python build.py`. Iz korena repozitorijuma pokrenuti i `Rscript analysis/verify.R` za nezavisnu proveru.
""")
    code("""from pathlib import Path
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
""")
    md("""Objavljene procene dve glavne liste su 47,40% i 40,00%, a granice intervala 45,3–49,5% i 37,9–42,1%. Poluširina oba intervala je 2,10 procentnih poena. RIK referentni procenti su 38,97% i 53,03%.

U ukupnih 3.624 ulaze i osobe koje nisu navele listu. Nije objavljena relevantna neponderisana baza opredeljenih, varijansa nakon ponderisanja, dizajn-efekat niti model spajanja telefonskog i onlajn uzorka. Iz margine se može izvesti *varijansno ekvivalentna* veličina jednostavnog slučajnog uzorka, ali to nije rekonstrukcija stvarnog broja opredeljenih. Ni 95% interval sam ne identifikuje raspodelu greške van tog intervala.

## 2. Model i događaj koji računamo

Udeo izražavamo u procentnim poenima. Za izabranu referencu θ pretpostavljamo procenu Q sa raspodelom `Normal(θ, SE²)`, gde je `SE = m / Φ⁻¹(0,975)`, a `m` objavljena poluširina 95% intervala. Referentni RIK udeo tretira se kao fiksiran: ova analiza ne proverava integritet izbornog brojanja.

Za opaženu razliku `d = q − θ` računamo `z = d/SE` i **dvostrani događaj** `|Q − θ| ≥ |d|`. Verovatnoća u tom modelu je `p = 2 Φ(−|z|) = erfc(|z|/√2)`. Ovo nije verovatnoća tačno jedne vrednosti, niti posteriorna verovatnoća hipoteze.

Numerički koristimo `erfc`, bez nestabilnog izraza `1 − Φ(z)`, koji za velike z može vratiti nulu zbog zaokruživanja u računaru. Numerički precizan normalni rep i opravdanost normalnog modela dva su odvojena pitanja.
""")
    code("""for h in r["headlines"]:
    print(h["list"])
    for key in ["error_pp", "margin_95_pp", "se_pp", "signed_z", "two_sided_p", "one_in", "variance_equivalent_n"]:
        print(f"  {key}: {h[key]:.15g}")
""")
    md(primary_table()+"\n*RIK: privremeni objavljeni procenti u sačuvanom preseku. Negativan znak razlike za Studentsku listu znači potcenjivanje.\n\nZa SNS dobijamo oko 1 u 277,2 biliona, zaokruženo 280 biliona. Rezultat za Studentsku listu prikazan je odvojeno. **Te dve verovatnoće ne množimo:** udeli lista iz iste ankete zavise jedan od drugog. Ovo nije zajednički test svih lista, a prikaz je naknadna dijagnostika, ne unapred registrovan test.")
    code('display(Image(filename=str(root / "docs/assets/02-normalna-dve-ose.png")))')
    md("""## 3. Loto 7/39: precizna definicija poređenja

Pretpostavljamo ravnopravne kombinacije. Jedna kombinacija je neuređen skup od sedam različitih brojeva među 39, pa je broj mogućnosti `C(39,7)`. Za jednu unapred izabranu kombinaciju u jednom izvlačenju, `p₁ = 1/C(39,7)`. Za po jednu kombinaciju u dva unapred određena nezavisna izvlačenja, `p₂ = p₁²`.

Ne računamo dve pobede bilo kada, sve igrače zajedno, veliki broj listića, sisteme ili dodatne igre. Kombinacije ne moraju biti iste u oba izvlačenja; bitno je da je po jedna izabrana pre svakog relevantnog nezavisnog izvlačenja.
""")
    code("""combinations = math.comb(39, 7)
p_single = 1 / combinations
p_double = p_single ** 2
p_sns = r["headlines"][0]["two_sided_p"]
print("Broj kombinacija:", combinations)
print("Jedna sedmica:", p_single)
print("Dve sedmice:", p_double)
print("Jednom u:", combinations ** 2)
print("Jedna sedmica / SNS p:", p_single / p_sns)
print("Dve sedmice / SNS p:", p_double / p_sns)
""")
    md(f"Dve sedmice imaju verovatnoću {sci(LOT['two_independent_p'])}; to je oko {sr(LOT['double_over_sns_p'],3)} puta verovatnije od SNS događaja u normalnom modelu. Poređenje se odnosi na veličinu dva broja. Ne čini modele ekvivalentnim niti opravdava pretpostavke ankete.")
    code('display(Image(filename=str(root / "docs/assets/03-loto-poredjenje.png")))')
    md("""## 4. Osetljivost na širinu greške

Ako je stvarna standardna greška `k` puta veća od izvedene, tada je novi z jednak `z/k`. Množilac standardne greške nije isto što i dizajn-efekat na varijansu: `DEFF = k²` u ovom pojednostavljenom poređenju. Scenariji nisu procene stvarnog DEFF-a. Oni ne ispravljaju sistematsku pristrasnost, već menjaju samo rasipanje oko nepromenjenog centra.
""")
    code("""for h in r["headlines"]:
    print(h["list"])
    for s in h["se_multipliers"]:
        print(f'  k={s["multiplier"]:3g}: z={s["abs_z"]:.6f}; p={s["two_sided_p"]:.12g}')
    print("  k potreban za p=0.05:", h["se_factor_to_reach_p_05"])
""")
    md(table(["Množilac SE","SNS: p","Studentska: p"],[[sr(a['multiplier'],1),sci(a['two_sided_p']),sci(b['two_sided_p'])] for a,b in zip(SNS['se_multipliers'],SL['se_multipliers'])])+f"\nZa SNS, k ≈ {sr(SNS['se_factor_to_reach_p_05'],3)} dovodi odstupanje do granice centralnih 95%; za Studentsku listu k ≈ {sr(SL['se_factor_to_reach_p_05'],3)}. To ne dokazuje da su stvarne greške toliko velike.")
    code('display(Image(filename=str(root / "docs/assets/04-osetljivost.png")))')
    md("""### Zaokruživanje objavljene margine

Preciznost ulaza ne opravdava mnogo značajnih cifara u javnoj tvrdnji. Kao jednostavnu proveru menjamo marginu od 2,05 do 2,15 pp, uz fiksirane objavljene procente. Ovo je scenario zaokruživanja margine, ne puna zajednička optimizacija svih zaokruženih procenata i krajeva intervala, i ne interval pouzdanosti za p.
""")
    code("""for item in r["headlines"][0]["rounded_margin_sensitivity"]:
    print(f'margina={item["margin_95_pp"]:.2f}; p={item["two_sided_p"]:.12g}; 1/p={item["one_in"]:.12g}')
""")
    md("""## 5. Isti 95% interval ne znači iste repove

Normalnost je dodatna pretpostavka. Kao matematički kontraprimer uzimamo simetrične Studentove t-raspodele sa 5, 10 i 30 stepeni slobode i skaliramo svaku tako da njen **centralni 95% interval takođe bude ±2,10 pp**. Za t-raspodelu skala nije standardna devijacija. Ove raspodele nisu fitovane na Ipsosove podatke i ne tvrdimo da opisuju njegov uzorak.

Njihovi repovi pokazuju zašto 95% interval sam ne identifikuje verovatnoću na 7,87 normalnih standardnih grešaka. Studentova t-raspodela ovde nema veze sa nazivom Studentske liste.
""")
    code("""for s in scenarios():
    print(f't(df={s["df"]}): skala={s["scale_pp"]:.9g} pp; dvostrano p={s["p"]:.12g}')
print("Normalni model:", r["headlines"][0]["two_sided_p"])
""")
    md(table(["Model sa istim centralnim 95% intervalom","SNS: dvostrano p"],[[f"Student t, df={a['df']}",sci(a['p'])] for a in scenarios()]+[["Normalni",sci(SNS['two_sided_p'])]])+"\nOva provera ograničava tumačenje glavnog broja: vrlo mali normalni rep ne može bez dodatnih dokaza postati stvarna verovatnoća događaja u anketi.")
    md("""## 6. Obuhvat birača i važeći glasovi

Ipsos isključuje Kosovo i Metohiju i građane koji žive u inostranstvu, dok nacionalni RIK presek obuhvata i te rezultate. Pored toga, Ipsos u objavljene udele ugrađuje pretpostavljenih 2,5% nevažećih listića. **Ne treba tvrditi da je Ipsos objavio samo važeće glasove:** njegovih 18 udela sabira se do 97,5%. Nacionalni RIK procenti takođe obuhvataju nevažeće u osnovici; broj izašlih birača nije nužno jednak broju listića u kutijama. Ne rekonstruišemo imenitelj prosto deljenjem brojem izašlih.

Za transparentnu dodatnu proveru koristimo same brojeve glasova za 18 lista: oduzmemo glasove na Kosovu i u inostranstvu, pa izračunamo udele među preostalim **važećim** glasovima. Ipsosove procente delimo sa 0,975. Ako istu normalnu pretpostavku prenosimo na novu skalu, **i standardnu grešku delimo sa 0,975**. To je uslovna transformacija sa fiksiranim faktorom, ne nova procena varijanse.

Oduzimanje regionalnih glasova približava geografsku osnovu; ne garantuje identičnu populaciju ispitanika, biračkih spiskova i onih koji su glasali, niti usklađuje trenutak merenja.
""")
    code("""print("Važeći glasovi, nacionalno:", r["national_valid_votes"])
print("Važeći glasovi, bez KiM i inostranstva:", r["matched_valid_votes"])
for g in r["geography_valid_vote_scenarios"]:
    print(g["list"])
    for key in ["estimate_percent", "benchmark_percent", "error_pp", "se_pp", "abs_z", "two_sided_p"]:
        print(f"  {key}: {g[key]:.12g}")
""")
    md(table(["Lista","Ipsos, važeći %","RIK, približen obuhvat i važeći %","Razlika pp","Uslovno normalno p"],[[g['list'],sr(g['estimate_percent'],4),sr(g['benchmark_percent'],4),sr(g['error_pp'],4),sci(g['two_sided_p'])] for g in RESULT['geography_valid_vote_scenarios']])+"\nOva korekcija ne uklanja veliku razliku. Ipak, primarni broj 1 u 280 biliona ostaje jasno označen kao račun iz objavljenih procenata, a ne rezultat ove dodatne transformacije.")
    md(f"""## 7. Istorijski dodatak: predsednički izbori 2012.

[Tanjugova vest preneta na B92, 11.05.2012.]({INP['historical_2012']['poll_source']}) navodi Ipsosovih 58% za Borisa Tadića i 42% za Tomislava Nikolića, na ukupnom uzorku 1.198, sa istraživanjem 10. maja. Drugi krug održan je 20. maja, dakle deset dana kasnije. [Publikacija RZS/RIK]({INP['historical_2012']['result_source']}) daje 1.481.952 i 1.552.063 glasa (štampana strana 80, 84. stranica PDF-a).

Na osnovici glasova za dva kandidata, Tadić ima {sr(RESULT['historical_2012']['two_candidate_share']*100,5)}%, pa je razlika oko {sr(RESULT['historical_2012']['error_pp'],4)} pp. Nemamo originalnu metodološku dokumentaciju, objavljenu marginu ili stvarni broj opredeljenih. Zato ne primenjujemo marginu iz 2026. niti govorimo da smo izračunali stvarnu verovatnoću te ankete.

Sledi samo ilustracija: `X ~ Binomial(n, p₀)`, gde je p₀ konačni udeo glasova za Tadića među dva kandidata. Računamo `P(X ≥ ceil(nq))`. Prikazujemo hipotetička n = 1.198, 655 i 300; n = 655 nije utvrđen uzorak opredeljenih, već scenario. Pragovi su q = 0,58 i q = 0,575; drugi dopušta donji rub zaokruživanja na 58% na ceo procenat.
""")
    code("""print("Referentni udeo za Tadića:", r["historical_2012"]["two_candidate_share"])
for h in r["historical_2012"]["scenarios"]:
    print(f'n={h["n_assumed"]}; prag={h["threshold"]}; k={h["k"]}; gornji rep={h["upper_tail"]:.12g}')
""")
    md("Ovo su **jednostrani binomni repovi**, sa drugačijim modelom od glavnog dvostranog normalnog računa za 2026. Ne množimo ove verovatnoće sa onima za 2026, ne tretiramo dva odabrana slučaja kao reprezentativan uzorak rada agencije i iz njih ne izvodimo zaključak o nameri. Promene tokom deset dana, izlaznost i nepoznata relevantna baza posebno ograničavaju istorijsko poređenje.")
    md("""## 8. Računske provere i šta bi omogućilo potpunu reviziju

Glavni normalni rep proverava se pomoću Python `math.erfc`, SciPy `norm.sf` i nezavisnog R `pnorm`. Istorijska binomna suma proverava se sa SciPy `binom.sf` i R `pbinom`. Testovi obuhvataju izvorne zbirove glasova, transformaciju osnovice i kombinatorni račun za Loto. Pokretanje: `python -m unittest discover -s tests -v`.

Računsko slaganje potvrđuje implementaciju zadatog modela. Ne potvrđuje da pretpostavke važe za stvarnu anketu. Za reviziju su potrebni relevantni brojevi ispitanika po modu i izbornoj opredeljenosti, upitnik, postupak izbora i regrutovanja, odziv, ponderi, model izlaznosti, postupanje sa neodlučnima i način izvođenja intervala. Anonimizovani podaci i dokumentacija omogućili bi proveru, uz zaštitu ispitanika.

Ne zaključujemo o profesionalnom ili pravnom prekršaju samo iz p-vrednosti. Ne tvrdimo da su kasne promene ili drugi izvori greške isključeni. Zajednički multinomni test nije predmet ove analize.
""")
    code("""from scipy.stats import norm, binom
for h in r["headlines"]:
    other = 2*norm.sf(h["abs_z"])
    assert math.isclose(other, h["two_sided_p"], rel_tol=1e-12)
for h in r["historical_2012"]["scenarios"]:
    other = binom.sf(h["k"]-1,h["n_assumed"],r["historical_2012"]["two_candidate_share"])
    assert math.isclose(other,h["upper_tail"],rel_tol=1e-10)
print("Nezavisne SciPy provere: sve prošle.")
""")
    md(source_section())
    md("## Dodatak: izvorni kod osnovnog računa\n\nIspod je ceo modul `analysis/core.py`. Isti modul se koristi za tabele, rezultate i grafikone. Kod iz ovog dodatka čita se u kontekstu datoteke; notebook ga uvozi u prvom izvršnom koraku.")
    md("```python\n"+(ROOT/"analysis/core.py").read_text(encoding="utf-8")+"\n```")
    for idx,c in enumerate(cells): c["id"]=hashlib.sha256((str(idx)+c["source"]).encode()).hexdigest()[:12]
    return cells


CSS="""
:root{--ink:#172840;--muted:#596b80;--blue:#215bc5;--red:#ac3e35;--line:#dce3ed;--paper:#fff;--bg:#f4f6fa}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:18px/1.7 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:var(--blue);text-decoration-thickness:1px;text-underline-offset:3px}a:hover{color:var(--red)}nav{background:var(--ink);color:white;padding:17px 24px;display:flex;gap:24px;justify-content:center;flex-wrap:wrap;font-size:14px}nav a{color:#fff;text-decoration:none}nav a:hover{color:#c4d9ff}
main{max-width:1100px;margin:40px auto;background:var(--paper);padding:58px 72px 60px;border:1px solid var(--line);border-radius:14px;box-shadow:0 4px 28px #17284005}h1{font-size:clamp(32px,4vw,49px);line-height:1.17;letter-spacing:-.035em;margin:18px 0 24px}h2{font-size:28px;line-height:1.3;margin:48px 0 18px;letter-spacing:-.018em}h3{font-size:21px;margin-top:32px}p{margin:18px 0}strong{font-weight:700}.lead{font-size:23px;line-height:1.55;color:var(--muted)}.eyebrow{font-size:12px;letter-spacing:.13em;color:var(--blue);font-weight:750}.callout{border-left:4px solid var(--red);padding:20px 24px;background:#fbefeb;border-radius:0 8px 8px 0;font-size:17px;margin:30px 0}.formula{padding:22px;background:#edf3fe;border:1px solid #d2dff7;border-radius:10px;font-size:21px;color:#174895;overflow:auto}.figure img,img{max-width:100%;height:auto;border-radius:8px}img{margin:12px 0}ul,ol{padding-left:25px}li{margin:9px 0}.table-scroll{overflow-x:auto;margin:25px 0}table{width:100%;border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums}th{background:#eaf0f8;text-align:left;font-size:12px;letter-spacing:.025em}td,th{padding:13px 12px;border-bottom:1px solid var(--line);vertical-align:top}tr:nth-child(even){background:#f8fafc}pre{white-space:pre;overflow:auto;background:#12223b;color:#edf4ff;padding:20px;border-radius:8px;font:13px/1.65 ui-monospace,SFMono-Regular,Consolas,monospace}code{font: .88em ui-monospace,SFMono-Regular,Consolas,monospace;background:#edf1f7;padding:.15em .3em;border-radius:3px}pre code{background:none;padding:0;color:inherit}details{border:1px solid var(--line);border-radius:8px;margin:22px 0;padding:10px 16px}summary{cursor:pointer;font-size:14px;font-weight:650;color:var(--blue)}.output{background:#f2f5fa;color:var(--ink);border:1px solid var(--line)}footer{max-width:1000px;padding:0 24px 45px;margin:auto;color:var(--muted);font-size:13px}sup{font-size:.72em}blockquote{margin:25px 0;border-left:3px solid var(--blue);padding:4px 20px;color:var(--muted)}.toc{font-size:14px;background:#f6f8fc;padding:16px 20px;border-radius:8px}.toc ul{margin:0}.download{display:inline-block;padding:10px 16px;margin:5px 10px 5px 0;border:1px solid var(--line);border-radius:7px;text-decoration:none}
@media(max-width:700px){body{font-size:17px}main{margin:0;padding:32px 22px;border:none;border-radius:0}nav{justify-content:flex-start;gap:12px 20px;padding:14px 20px;font-size:12px}h2{font-size:25px}.lead{font-size:20px}.formula{font-size:17px}table{min-width:580px}.callout{padding:16px 18px}footer{padding-top:25px}}
@media print{nav,details{display:none}body{background:white;font-size:12px}main{border:0;margin:0;padding:0;max-width:none;box-shadow:none}h1{font-size:28px}h2{font-size:20px}img{break-inside:avoid}a{color:inherit}}
"""


def md_html(text):
    result=markdown.markdown(text,extensions=["tables","fenced_code","toc"],output_format="html5")
    return result.replace("<table>",'<div class="table-scroll"><table>').replace("</table>","</table></div>")


def embed_assets(body):
    import re
    def sub(m):
        raw=(DOCS/m.group(1)).read_bytes()
        return 'src="data:image/png;base64,'+base64.b64encode(raw).decode()+'"'
    return re.sub(r'src="(assets/[^"<>]+\.png)"',sub,body)


def page(title,body,name):
    nav='<nav aria-label="Glavna navigacija"><a href="index.html">Sažetak za javnost</a><a href="statistika-101.html">Statistika 101</a><a href="tehnicki.html">Python i metodologija</a><a href="provera-r.html">Provera u R-u</a><a href="'+REPO+'">GitHub ↗</a></nav>'
    desc="Uslovni normalni račun iz objavljene margine Ipsosa, poređenje sa Lotom 7/39, pretpostavke i reproduktivan kod."
    return f'''<!doctype html><html lang="sr-Latn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · Mihajlo Popesku</title><meta name="description" content="{desc}"><meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{desc}"><meta property="og:type" content="article"><meta property="og:url" content="{SITE+name}"><meta property="og:image" content="{SITE}assets/03-loto-poredjenje.png"><meta name="twitter:card" content="summary_large_image"><style>{CSS}</style></head><body>{nav}<main>{embed_assets(body)}</main><footer>Mihajlo Popesku · verzija 1.0.0 · 01.11.2026.<br>RIK: privremeni presek 30.10.2026. u 09:10. Modelski račun nije verovatnoća nameštanja.<br><a href="{REPO}/issues">Prijavite proverljivu grešku ili predložite ispravku</a> · <a href="{REPO}/blob/main/data/PROVENANCE.md">Poreklo podataka</a></footer></body></html>'''


def render_notebook(nb):
    parts=['<div class="eyebrow">TEHNIČKI IZVEŠTAJ · IZVRŠENI PYTHON NOTEBOOK</div>',
           '<p><a class="download" href="analiza.ipynb">Preuzmi notebook</a><a class="download" href="results.json">Preuzmi rezultate</a></p>']
    for c in nb.cells:
        if c.cell_type=="markdown":
            parts.append(md_html(c.source))
        else:
            parts.append('<details><summary>Prikaži izvršeni Python kod</summary><pre><code>'+html.escape(c.source)+'</code></pre></details>')
            for output in c.get("outputs",[]):
                if output.output_type=="error":raise RuntimeError(output)
                if output.output_type=="stream":parts.append('<pre class="output">'+html.escape(output.text)+'</pre>')
                elif "image/png" in output.get("data",{}):parts.append('<img alt="Grafikon iz izvršenog notebooka" src="data:image/png;base64,'+output.data["image/png"]+'">')
                elif "text/html" in output.get("data",{}):parts.append(output.data["text/html"])
                elif "text/plain" in output.get("data",{}):parts.append('<pre class="output">'+html.escape(output.data["text/plain"])+"</pre>")
    body="\n".join(parts)
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(body,"html.parser")
    toc='<div class="toc"><strong>Sadržaj tehničkog izveštaja</strong><ul>'+''.join(
        '<li><a href="#'+html.escape(h['id'])+'">'+html.escape(h.get_text())+'</a></li>'
        for h in soup.find_all('h2',id=True))+'</ul></div>'
    # Put the table of contents after the introductory material, before section 1.
    first=body.find('<h2 ')
    return body[:first]+toc+body[first:]


def r_report():
    path=ROOT/"r_verification.csv"
    if not path.exists():raise RuntimeError("Run Rscript analysis/verify.R before publishing the R report.")
    rows=list(csv.DictReader(path.open(encoding="utf-8")))
    for py,rr in zip(RESULT["headlines"],rows):
        assert math.isclose(py["two_sided_p"],float(rr["p"]),rel_tol=1e-10)
    return f"""<div class="eyebrow">NEZAVISNA RAČUNSKA PROVERA</div>

# Isti račun u R-u

Python i R nezavisno računaju standardnu grešku, z i normalni rep iz istih ulaznih procenata i margina. Ovaj dokument proverava numerički rezultat. Puna interpretacija i osetljivost nalaze se u [tehničkom izveštaju](tehnicki.html).

{table(['Lista','Python p','R p','Relativna razlika'],[[p['list'],sci(p['two_sided_p'],7),sci(float(rr['p']),7),f"{abs(p['two_sided_p']-float(rr['p']))/p['two_sided_p']:.2e}"] for p,rr in zip(RESULT['headlines'],rows)])}

Razlike su na nivou numeričkog zaokruživanja. Saglasnost dve implementacije ne potvrđuje pretpostavke modela. Glavni broj je približan normalni modelski rezultat, a ne „tačna verovatnoća stvarne ankete“.

## Kod za ponovno pokretanje

Pokrenuti iz korena repozitorijuma: `Rscript analysis/verify.R`. Potreban je samo osnovni R, bez dodatnih paketa. Prva objava proverena je u R-u 4.2.2. Skripta čita CSV datoteke izvedene iz `data/inputs.json`; testovi proveravaju njihovu saglasnost.

```r
{(ROOT/'analysis/verify.R').read_text(encoding='utf-8')}
```

Skripta proverava i istorijske binomne scenarije za 2012. i transformaciju na približen geografski obuhvat i važeće glasove. Izlazi su [r_verification.csv]({REPO}/blob/main/r_verification.csv), [r_historical_verification.csv]({REPO}/blob/main/r_historical_verification.csv) i [r_geography_verification.csv]({REPO}/blob/main/r_geography_verification.csv).

## Zašto nema množenja rezultata za SNS i Studentsku listu?

Udeli iz iste ankete nisu nezavisni. Zato ih prikazujemo pojedinačno. Množenje dve verovatnoće opravdano je u našem Loto poređenju jer smo eksplicitno definisali dva nezavisna izvlačenja, ali nije opravdano samo zato što postoje dva stranačka udela ili dve izabrane godine.
"""


def readme():
    return f"""# Ipsos, verovatnoća i Loto

**Uslovna normalna analiza objavljenih izbornih procena 2026.**  
Autor: **Mihajlo Popesku** · verzija **1.0.0** · **01.11.2026.**

## Čitajte onlajn

| Dokument | Sadržaj |
| --- | --- |
| [Sažetak za javnost]({SITE}) | Glavni nalazi, grafikoni i poređenje sa Lotom, na srpskom. |
| [Statistika 101]({SITE}statistika-101.html) | Uzorkovanje, standardna greška, dve ose, repovi i račun korak po korak. |
| [Tehnički Python izveštaj]({SITE}tehnicki.html) | Izvršeni kod, pretpostavke, podaci, osetljivost, geografska provera i istorijski dodatak. |
| [Provera u R-u]({SITE}provera-r.html) | Nezavisna numerička provera istih ulaza. |

## Glavni rezultat i njegovo značenje

Za SNS, Ipsosovih **47,40%** naspram RIK-ovih **38,97%** daje razliku od **8,43 pp**. Iz objavljene margine **±2,10 pp na 95%** izvodimo `SE = 2.10 / 1.9599639845 = 1.071448... pp`, pa `z = 8.43 / SE = 7.867855...`.

U **normalnom modelu**, verovatnoća jednako velikog ili većeg odstupanja u bilo kom smeru iznosi **p ≈ 3,6077 × 10⁻¹⁵**, odnosno oko **1 u 277,2 biliona**, zaokruženo **1 u 280 biliona**. Bilion ovde znači 10¹².

> Ovo je uslovna dijagnostika modela izvedenog iz objavljene margine. Nije utvrđena verovatnoća greške stvarne ankete, verovatnoća hipoteze ili verovatnoća nameštanja. Sam 95% interval ne identifikuje ekstremne repove raspodele.

{primary_table()}

*RIK: **privremeni presek 30.10.2026. u 09:10**, 8.339/8.392 biračka mesta. Ne konačni rezultati. Dve marginalne verovatnoće se **ne množe**.

![Normalna raspodela sa dve ose](docs/assets/02-normalna-dve-ose.png)

## Poređenje sa Lotom 7/39

`C(39,7) = {LOT['combinations']}`. Za jednu kombinaciju u jednom izvlačenju, sedmica ima verovatnoću `1 / {LOT['combinations']}`. Za po jednu kombinaciju u **dva unapred određena nezavisna izvlačenja**, dve sedmice imaju verovatnoću `1 / {LOT['combinations']}² = {LOT['two_independent_p']:.12g}`, tj. **1 u 236,6 biliona**.

To je približno isti red veličine kao naš SNS normalni rep; dve sedmice su oko **1,17 puta verovatnije**. Jedna sedmica je oko **18,0 miliona puta verovatnija**. Poređenje ne odnosi se na mnogo kombinacija ili dve pobede bilo kada i ne potvrđuje model ankete.

![Poređenje sa Lotom](docs/assets/03-loto-poredjenje.png)

## Provere i ograničenja

- Standardna greška proizlazi iz objavljene margine, ne iz pretpostavke da svih 3.624 ispitanika ulazi u stranačke udele. Relevantna neponderisana baza nije objavljena.
- Model pretpostavlja istu ciljnu populaciju i podršku, odsustvo pristrasnosti, ispravnu objavljenu preciznost i normalne repove. Neodaziv, ponderisanje, izlaznost i kasne promene nisu obuhvaćeni prostim normalnim repom.
- Pokazujemo scenarije sa većom standardnom greškom, zaokruživanjem margine i drugačijim oblikom raspodele sa istim centralnim 95% intervalom.
- Posebno prikazujemo udele među važećim glasovima bez rezultata KiM i inostranstva. To približava obuhvat; ne rekonstruiše ceo dizajn ankete.
- Dodatak za 2012. je jasno označen kao ilustrativan binomni scenario sa nepoznatom relevantnom bazom i desetodnevnim razmakom. Ne spajamo ga u „zajedničku verovatnoću“ sa 2026.
- Račun ne utvrđuje uzrok odstupanja ili nameru. Za potpunu reviziju potrebna je metodologija i odgovarajuće anonimizovani podaci.

## Ponovite račun

Osnovni račun, **bez instaliranja biblioteka**, Python ≥3.11:

```bash
python analysis/core.py
```

Za sve grafikone, izvršeni notebook, izveštaje i nezavisnu R proveru:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis/core.py
Rscript analysis/verify.R
python build.py
python -m unittest discover -s tests -v
```

R ≥4.2; dodatni R paketi nisu potrebni. Za punu izradu preporučen je Python 3.12. Ne pokreću se masovne simulacije: normalni rep se računa direktno. `build.py` izvršava notebook, ugrađuje grafikone u samostalne HTML datoteke i piše provere okruženja. Bez pristupa mreži tokom analize, nakon instalacije biblioteka.

## Sadržaj repozitorijuma

| Putanja | Namena |
| --- | --- |
| `data/inputs.json` | Jedinstveni izvor ulaznih brojki i metapodataka. |
| `data/PROVENANCE.md`, `data/evidence/` | Poreklo i sačuvani tekst javnih RIK prikaza. |
| `analysis/core.py` | Osnovni normalni, Loto, geografski i istorijski račun. |
| `analysis/shape_sensitivity.py` | Kontraprimeri: isti 95% interval, drugačiji repovi. |
| `analysis/figures.py` | Reproduktivni matplotlib PNG/SVG grafikoni. |
| `analysis/verify.R` | Nezavisna provera u osnovnom R-u. |
| `analiza.ipynb` | Izvršeni Jupyter notebook. |
| `reports/` | Čitljivi tekstovi izveštaja u Markdown formatu. |
| `docs/` | Samostalni HTML izveštaji za GitHub Pages i preuzimanja. |
| `results.json`, `shape_sensitivity.json` | Mašinski čitljivi rezultati. |
| `tests/` | Matematičke, međujezičke i dokumentacione provere. |

GitHub Pages se služi sa `main:/docs`. Za ispravku podataka izmeniti `data/inputs.json`, navesti novi presek i verziju, pa ponoviti sve korake. Pri promeni ulaza pregledati i ažurirati autorski tekst i oznake grafikona u `build.py` i `analysis/figures.py`: objašnjenja i zaokruženi natpisi vezani su za ovu verziju podataka. Ranije verzije ostaju u Git istoriji.

## Izvori, autorstvo i citiranje

Primarni izvori: [Ipsos]({INP['poll']['source']}), [RIK]({INP['rik']['source']}) i [Državna lutrija Srbije](https://lutrija.rs/Help/Instructions?helpTypeId=1). Detalji i istorijski izvori su u `data/PROVENANCE.md` i tehničkom izveštaju.

Ovaj paket razvija [autorovo objašnjenje na X-u]({POST}). Organizacija javnog sažetka, tehničkog dokumenta i otvorenog koda inspirisana je [radom Gorana S. Milovanovića]({REF}); njegov multinomni postupak i rezultati nisu preuzeti kao naš račun. Tekst i kod napisani su za ovaj pristup.

Citirati: **Popesku, M. (2026). Ipsos, verovatnoća i Loto: uslovna normalna analiza izbornih procena 2026. Verzija 1.0.0.** Navesti link, verziju i datum korišćenog RIK preseka. `CITATION.cff` sadrži metapodatke. Primarni izvori zadržavaju svoja prava.

Za proverljivu grešku otvorite Issue sa tačnom datotekom, ulazom i predloženom ispravkom. Ne dodajte lične podatke ispitanika.
"""


def main():
    core.export(RESULT)
    generate()
    shape=scenarios()
    (ROOT/"shape_sensitivity.json").write_text(json.dumps(shape,indent=2)+"\n")
    # Execute actual cells, including independent numerical checks.
    nb=nbformat.v4.new_notebook(cells=technical_cells(),metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":platform.python_version()}})
    if "--skip-execution" in sys.argv:
        raise RuntimeError("Publication must use an executed notebook; skip-execution is disabled.")
    print("Executing notebook...",flush=True)
    NotebookClient(nb,timeout=120,kernel_name="python3",resources={"metadata":{"path":str(ROOT)}}).execute()
    nbformat.write(nb,ROOT/"analiza.ipynb")
    print("Notebook executed.",flush=True)
    for name,title,content in [("index.html","Šta znači 1 u 280 biliona?",summary()),("statistika-101.html","Statistika 101: uzorak, greška i verovatnoća",primer()),("provera-r.html","Nezavisna provera u R-u",r_report())]:
        (DOCS/name).write_text(page(title,md_html(content),name),encoding="utf-8")
        import re
        report_md=content.replace('(assets/','(../docs/assets/')
        report_md=re.sub(r'\((index|statistika-101|tehnicki|provera-r)\.html',lambda m:'('+SITE+m.group(1)+'.html',report_md)
        report_md=report_md.replace('(analiza.ipynb)','(../analiza.ipynb)').replace('(results.json)','(../results.json)')
        (ROOT/"reports"/(name.replace(".html",".md"))).write_text(report_md,encoding="utf-8")
    (DOCS/"tehnicki.html").write_text(page("Tehnička analiza i izvršeni Python notebook",render_notebook(nb),"tehnicki.html"),encoding="utf-8")
    (ROOT/"reports/tehnicki.md").write_text("\n\n".join(c.source if c.cell_type=="markdown" else "```python\n"+c.source+"\n```" for c in nb.cells),encoding="utf-8")
    (ROOT/"README.md").write_text(readme(),encoding="utf-8")
    for file in ["analiza.ipynb","results.json","shape_sensitivity.json"]:shutil.copy2(ROOT/file,DOCS/file)
    (DOCS/".nojekyll").touch()
    environment={"python":platform.python_version(),"platform":platform.platform(),"input_sha256":RESULT["input_sha256"],"code_cells_executed":sum(c.cell_type=="code" for c in nb.cells),"packages":{}}
    from importlib.metadata import version
    for name in ["matplotlib","numpy","scipy","nbformat","nbclient","nbconvert","ipykernel","Markdown"]:environment["packages"][name]=version(name)
    (ROOT/"build_environment.json").write_text(json.dumps(environment,indent=2)+"\n")
    print("Built 4 HTML documents, executed notebook, 4 figures in PNG/SVG, and README.",flush=True)


if __name__=="__main__":main()
