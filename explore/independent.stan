data {
    int<lower=0> J;
    int<lower=0> n[J];
    int<lower=0> y[J];
}
parameters {
    real<lower=0,upper=1> phi;
    real<lower=0.1> lambda;
    real<lower=0,upper=1> theta[J];
}
transformed parameters {
    real<lower=0> alpha;
    real<lower=0> beta;
    alpha = lambda * phi;
    beta = lambda * (1 - phi);
}
model {
    phi ~ beta(1,1);
    lambda ~ pareto(0.1, 1.5);
    theta ~ beta(alpha, beta);
    y ~ binomial(n, theta);
}
generated quantities {
    real thetaP;
    thetaP = beta_rng(alpha, beta);
}
