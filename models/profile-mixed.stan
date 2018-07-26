data {
    int<lower=0> J;
    int<lower=0> n[J];
    int<lower=0> y[J];
}
parameters {
    real<lower=0> alpha;
    real<lower=0> beta;
    
    real mu;
    real<lower=0> sig2;
    
    real<lower=0, upper=1> mix;

    real<lower=0> nRate;
    real<lower=0,upper=1> theta[J];
}
model {
    mu ~ normal(0, 10);
    alpha ~ normal(0, 0.5);
    beta ~ normal(0, 0.5);
    
    target += 
        log_mix(mix,
                beta_lpdf(theta | alpha, beta),
                normal_lpdf(logit(theta) | mu, sig2));

    n ~ poisson(nRate);
    y ~ binomial(n, theta);
}
generated quantities {
    real thetaP;
    int<lower=0> nP;
    int<lower=0> yP;
    int pick;
    
    pick = categorical_rng([mix, 1-mix]');
    if (pick == 0) {
        thetaP = beta_rng(alpha, beta);
    } else {
        thetaP = inv_logit(normal_rng(mu, sig2));
    }
    nP = poisson_rng(nRate);
    yP = binomial_rng(nP, thetaP);
}
