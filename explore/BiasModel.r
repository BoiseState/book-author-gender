
library(tidyverse)
library(foreach)

model.prior = function(alpha, beta) {
    (alpha + beta) ^ (-5 / 2)
}

pure_loglike = function(alpha, beta, ys, ns) {
    base = lgamma(alpha + beta) - lgamma(alpha) - lgamma(beta)
    data = map2_dbl(alpha, beta, function(a, b) {
        sum(lgamma(a + ys) + 
                lgamma(b + ns - ys) - 
                lgamma(a + b + ns))
    })
    length(ys) * base + data
}
model.loglike = pure_loglike

if (library(rustinr, logical.return=TRUE)) {
    message("loading optimized likelihood model")
    rust(path='optimized-loglike.rs')
    model.loglike = fast_loglike
}

model.theta.post = function(theta, norm, counts, totals, loglike=model.loglike, prior=model.prior, max=Inf) {
    foreach(thv=theta, .combine=c) %dopar% {
        integrate(function(beta) {
            map_dbl(beta, function(bv) {
                integrate(function(alpha) {
                    print(alpha)
                    print(bv)
                    print(summary(counts))
                    ll = loglike(alpha, bv, counts, totals)
                    pth = dbeta(thv, alpha, bv)
                    res = exp(log(pth) + log(prior(alpha, bv)) + ll - norm)
                    res
                }, 1.0e-6, max, rel.tol = 0.001)$value
            })
        }, 1.0e-6, max, rel.tol = 0.001)$value
    }
}

par.beta = function(x, y) {
    exp(y) / (exp(x) + 1)
}
par.alpha = function(x, y) {
    exp(x) * par.beta(x, y)
}

xydensity = function(x, y, counts, totals, prior=model.prior, loglike=model.loglike) {
    crossing(x=x, y=y) %>%
        mutate(alpha = par.alpha(x, y),
               beta = par.beta(x, y)) %>%
        mutate(logPrior = log(prior(alpha, beta)),
               logLike = loglike(alpha, beta, counts, totals),
               rawLogPost = logPrior + logLike) %>%
        mutate(logJacobian = log(alpha) + log(beta),
               logPost = rawLogPost + logJacobian)
}

message("compiling independent Bayesian model")
indep_model = stan_model(file='independent.stan', auto_write=TRUE)
indep_model

message("compiling independent Bayesian model with logit-normal")
logit_norm_model = stan_model(file='logitnormal.stan', auto_write=TRUE)
logit_norm_model

message("compiling full Bayesian model")
full_model = stan_model(file='withrecs.stan', auto_write=TRUE)
full_model
