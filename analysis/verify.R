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
