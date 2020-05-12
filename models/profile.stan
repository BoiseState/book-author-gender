data {
    // The number of users
    int<lower=0> J;
    // Each user's number of known-gender books
    int<lower=5> n[J];
    // Each user's number of female-authored books
    int<lower=0> y[J];
}

parameters {
    // Mean of user profile bias
    real mu;
    // SD of user profile bias
    real<lower=0> sigma;
    // Users' smoothed biases, in log-odds
    vector[J] nTheta;
}

model {
    // prior distribution
    // put vague priors on everything
    mu ~ normal(0, 10);
    sigma ~ exponential(0.1);

    // likelihood model
    // users' female-authored books
    y ~ binomial(n, inv_logit(nTheta));
    // and users' smoothed biases!
    nTheta ~ normal(mu, sigma);
}

generated quantities {
    // compute log_lik for WAIC and friends
    real log_lik [J];
    // we want to draw synthetic users, with their smoothed biases
    // simulated proportions will be done in Python
    real<lower=0, upper=1> thetaP;
    
    thetaP = inv_logit(normal_rng(mu, sigma));

    for (i in 1:J) {
        log_lik[i] = binomial_lpmf(y[i] | n[i], inv_logit(nTheta[i]));
    }
}
