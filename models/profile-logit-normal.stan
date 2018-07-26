data {
    int<lower=0> J;
    int<lower=0> n[J];
    int<lower=0> y[J];
}
parameters {
    real mu;
    real<lower=0.01> sigma;
    
    real<lower=0> nMu;
    real<lower=0> nDisp;

    real nTheta[J];
}
transformed parameters {
    real<lower=0,upper=1> theta[J];
    theta = inv_logit(nTheta);
}
model {
    nMu ~ lognormal(0, 5);
    nDisp ~ lognormal(0, 5);
 
    mu ~ normal(0, 100);
    sigma ~ lognormal(0, 5);
 
    n ~ neg_binomial_2(nMu, nDisp);
    nTheta ~ normal(mu, sigma);
    y ~ binomial(n, theta);
}
generated quantities {
    real<lower=0, upper=1> thetaP;
    int<lower=0> nP;
    int<lower=0> yP;
    
    thetaP = inv_logit(normal_rng(mu, sigma));
    nP = neg_binomial_2_rng(nMu, nDisp);
    yP = binomial_rng(nP, thetaP);
}
