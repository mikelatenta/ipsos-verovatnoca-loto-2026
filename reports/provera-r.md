<div class="eyebrow">NEZAVISNA RAČUNSKA PROVERA</div>

# Isti račun u R-u

Python i R nezavisno računaju standardnu grešku, z i normalni rep iz istih ulaznih procenata i margina. Ovaj dokument proverava numerički rezultat. Puna interpretacija i osetljivost nalaze se u [tehničkom izveštaju](https://mikelatenta.github.io/ipsos-verovatnoca-loto-2026/tehnicki.html).

| Lista | Python p | R p | Relativna razlika |
| --- | --- | --- | --- |
| SNS / Ujedinjena Srbija | 3,6077215 × 10<sup>−15</sup> | 3,6077215 × 10<sup>−15</sup> | 7.00e-15 |
| Studentska lista | 5,0073712 × 10<sup>−34</sup> | 5,0073712 × 10<sup>−34</sup> | 3.79e-14 |


Razlike su na nivou numeričkog zaokruživanja. Saglasnost dve implementacije ne potvrđuje pretpostavke modela. Glavni broj je približan normalni modelski rezultat, a ne „tačna verovatnoća stvarne ankete“.

## Kod za ponovno pokretanje

Pokrenuti iz korena repozitorijuma: `Rscript analysis/verify.R`. Potreban je samo osnovni R, bez dodatnih paketa. Prva objava proverena je u R-u 4.2.2. Skripta čita CSV datoteke izvedene iz `data/inputs.json`; testovi proveravaju njihovu saglasnost.

```r
# Independent base-R check of the Python calculation. No additional packages.
# Run from the repository root: Rscript analysis/verify.R
x <- read.csv("data/headline.csv", check.names=FALSE, fileEncoding="UTF-8")
x$se <- x$margin/qnorm(.975)
x$z <- (x$estimate-x$benchmark)/x$se
x$p <- 2*pnorm(-abs(x$z))  # Direct lower tail, avoiding 1 - pnorm(z).
x$one_in <- 1/x$p
write.csv(x,"r_verification.csv",row.names=FALSE,fileEncoding="UTF-8")
print(x, digits=14)
cat("Loto combinations:",choose(39,7),"\n")
cat("Two preselected independent draws:",format(1/choose(39,7)^2,digits=15),"\n")
# 2012 is an illustrative binomial scenario, not a reconstruction of the survey.
n <- c(1198,655,300)
hist <- expand.grid(n=n,threshold=c(.58,.575))
hist$k <- ceiling(hist$n*hist$threshold-1e-12)
p0 <- 1481952/(1481952+1552063)
hist$upper_tail <- pbinom(hist$k-1,hist$n,p0,lower.tail=FALSE)
write.csv(hist,"r_historical_verification.csv",row.names=FALSE)
# Matched geography, valid votes; scale estimate AND SE by the same .975 factor.
v <- read.csv("data/rik_counts.csv",fileEncoding="UTF-8")
v$matched <- v$national_votes-v$kosovo_votes-v$overseas_votes
ix <- c(1,3)
estimate <- v$poll_percent[ix]/.975
benchmark <- 100*v$matched[ix]/sum(v$matched)
matched_se <- (2.1/.975)/qnorm(.975)
z <- (estimate-benchmark)/matched_se
write.csv(data.frame(estimate,benchmark,se=matched_se,z,p=2*pnorm(-abs(z))),
          "r_geography_verification.csv",row.names=FALSE)

```

Skripta proverava i istorijske binomne scenarije za 2012. i transformaciju na približen geografski obuhvat i važeće glasove. Izlazi su [r_verification.csv](https://github.com/mikelatenta/ipsos-verovatnoca-loto-2026/blob/main/r_verification.csv), [r_historical_verification.csv](https://github.com/mikelatenta/ipsos-verovatnoca-loto-2026/blob/main/r_historical_verification.csv) i [r_geography_verification.csv](https://github.com/mikelatenta/ipsos-verovatnoca-loto-2026/blob/main/r_geography_verification.csv).

## Zašto nema množenja rezultata za SNS i Studentsku listu?

Udeli iz iste ankete nisu nezavisni. Zato ih prikazujemo pojedinačno. Množenje dve verovatnoće opravdano je u našem Loto poređenju jer smo eksplicitno definisali dva nezavisna izvlačenja, ali nije opravdano samo zato što postoje dva stranačka udela ili dve izabrane godine.
