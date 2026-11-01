# Poreklo ulaznih podataka

`inputs.json` je jedinstveni izvor brojeva za analizu. `headline.csv` i `rik_counts.csv` nastaju iz njega; nezavisna R skripta čita ove CSV datoteke. Testovi proveravaju njihovo slaganje sa JSON-om.

## Ipsos, 2026.

Izvor je javno [saopštenje Ipsosa od 22.10.2026.](https://www.ipsos.com/sr-rs/rezultati-istrazivanja-pred-parlamentarne-izbore-oktobar-2026), dostupno i kao PDF. U lokalnoj radnoj dokumentaciji sačuvan je primerak PDF-a; njegov SHA-256 je naveden u `source_manifest.json`. Javni repozitorijum objavljuje transkribovane brojke i vezu ka originalu.

- Terenski rad: 20–22.10.2026; ukupni uzorak 3.624.
- Telefonski intervjui 90%, Ipsos onlajn panel 10%.
- Obuhvat: punoletni u Srbiji bez KiM i građana koji žive u inostranstvu.
- Udeli lista među opredeljenima, uz ugrađenu pretpostavku 2,5% nevažećih listića.
- Relevantni broj opredeljenih nije objavljen; ne zamenjujemo ga ukupnim n.
- Procene 18 lista i intervali prepisani su iz tabele; imena u CSV-u su skraćena i čuva se redni broj liste.

## RIK, 2026.

Izvor: [javni portal RIK-a](https://www.rik.parlament.gov.rs/542645/rezultati/), izbor „Parlamentarni 2026“.

Nacionalni prikaz sačuvan je 30.10.2026. sa oznakom portala **09:10:00**, 8.339 od 8.392 obrađena biračka mesta. Udeli 38,97% i 53,03% u glavnom računu jesu objavljeni zaokruženi procenti, ne količnici dobijeni deljenjem brojem izašlih. Ranije dostavljena slika sa 8.331 mestom ima iste dve zaokružene vrednosti, ali za geografsku proveru koristimo kasnije brojeve glasova.

`data/evidence/` sadrži tekst javnih nacionalnih i regionalnih prikaza, izdvojen iz sačuvanog interfejsa. To su transkripti, a ne zvanični CSV izvoz. U `source_manifest.json` nalaze se kontrolni zbirovi izvornog sačuvanog prikaza i objavljenog tekstualnog izvoda. Regionalni prikazi sačuvani su 30.10.2026; ne predstavljamo ih kao novo čitanje živog portala 01.11.

Provera zbirova 18 lista: nacionalno 4.374.187 važećih glasova, KiM 34.791, inostranstvo 79.283. Posle oduzimanja ostaje 4.260.113. Svi pojedinačni brojevi nalaze se u JSON-u, CSV-u i transkriptima. Ne objavljujemo izvedeni „tačan“ broj nevažećih na osnovu zaokruženih procenata i ne mešamo broj birača koji su izašli sa brojem listića u kutijama.

Brojanje je u ovom izdanju **privremeno**. Analiza tretira korišćeni RIK presek kao referencu; ne proverava integritet izbornog brojanja. Konačni podaci zahtevaju novu označenu verziju, bez tihog menjanja reference.

## Loto 7/39

Pravilo izbora 7 brojeva od 39 provereno je preko [Državne lutrije Srbije](https://lutrija.rs/Help/Instructions?helpTypeId=1) i njene [stranice pravila](https://lutrija.rs/help/rules). Broj `C(39,7)` računamo iz pravila, ne preuzimamo tuđu procenu šanse. Poređenje pretpostavlja ravnopravne kombinacije, po jednu kombinaciju i unapred određena nezavisna izvlačenja. Cene listića, iznosi fonda i isplate nisu predmet analize.

## Istorijski dodatak 2012.

[Tanjug/B92, 11.05.2012.](https://www.b92.net/o/info/izbori2012/vesti?nav_id=608340): 58% Tadić, 42% Nikolić, ukupno n=1.198, istraživanje 10. maja. Ovo je posredni novinski izvor, a ne originalna tehnička dokumentacija agencije. Broj opredeljenih i objavljena margina nisu utvrđeni.

[RZS/RIK, Izbori maj 2012.](https://arhiva.rik.parlament.gov.rs/doc/arhiva/predsednik/2012/5.%202012%20publikacija%20rzs.compressed.pdf), štampana strana 80 / 84. PDF stranica: drugi krug 20.05.2012, Tadić 1.481.952 i Nikolić 1.552.063 glasa. Udeo računamo na osnovici glasova za dva kandidata. Hipotetičke binomne scenarije ne proglašavamo stvarnom verovatnoćom originalne ankete.

## Autorski i organizacioni kontekst

Paket razvija [objavu Mihajla Popeskua od 31.10.2026.](https://x.com/visokodrustvo/status/2116459194765246791). Struktura javnog sažetka, tehničkog dokumenta i koda inspirisana je [repozitorijumom Gorana S. Milovanovića](https://github.com/GoranMilovanovic/izboriRepublikaSrbija_20261025). Njegov multinomni model nije korišćen za naš glavni rezultat; tuđi kod i grafikoni nisu kopirani u ovaj paket.

Za metodološke zahteve transparentnosti konsultovani su [AAPOR standardi objavljivanja](https://aapor.org/standards-and-ethics/disclosure-standards/). Ovaj repozitorijum ne predstavlja presudu o kršenju kodeksa.
