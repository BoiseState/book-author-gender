// This file is generated from models.md
data {
    // The number of users
    int<lower=0> J;
    // Each user's number of known-gender books
    int<lower=5> n[J];
    // Each user's number of female-authored books
    int<lower=0> y[J];

    // Number of algorithms
    int<lower=0> A;
    // Number of recommendation lists
    int<lower=0> NL;
    // User for each rec list
    int<lower=1,upper=J> ru[NL];
    // Algorithm for each rec list
    int<lower=1,upper=A> ra[NL];
    // Number of known-gender books in each rec list
    int<lower=0> rn[NL];
    // Number of female-authored books in each rec list
    int<lower=0> ry[NL];

}
transformed data {
    // The model performs better when we model number of books 
    // _after 5_ from negative binomial
    int<lower=0> shiftN[J];

    // Recommendation list (smoothed) proportion female
    vector<lower=0,upper=1>[NL] rp;
    // The logit of the proportion (log odds)
    vector[NL] rll;

    for (i in 1:J) {
        shiftN[i] = n[i] - 5;
    }

    rp = (to_vector(ry) + 1) ./ (to_vector(rn) + 2);
    rll = logit(rp);
}
parameters {
    // Mean and dispersion of user profile sizes
    real<lower=0> nMean;
    real<lower=0> nDisp;

    // mean of user profile bias
    real mu;
    // SD of user profile bias
    real<lower=0> sigma;
    // Users' smoothed biases, in log-odds
    vector[J] nTheta;

    // Recommender response intercepts
    vector[A] recB;
    // Recommender response slopes
    vector[A] recS;
    // Recommender response variance
    vector<lower=0>[A] recV;
}
transformed parameters {
    // User smoothed biases, as proportions/probabilities
    vector<lower=0,upper=1>[J] theta;

    vector[NL] rbias;
    vector[NL] noiseR;

    theta = inv_logit(nTheta);

    rbias = recB[ra] + recS[ra] .* nTheta[ru];
    noiseR = rll - rbias;
}
model {
    // profile prior distribution
    nMean ~ exponential(0.001);
    nDisp ~ exponential(0.001);
    mu ~ normal(0, 100);
    sigma ~ exponential(0.001);

    // rec list priors
    recB ~ normal(0, 100);
    recS ~ normal(0, 100);
    recV ~ exponential(0.001);


    // profile likelihood model
    shiftN ~ neg_binomial_2(nMean, nDisp);
    y ~ binomial(n, theta);
    nTheta ~ normal(mu, sigma);

    // rec list likelihood model - noise and binomial choice
    noiseR ~ normal(0, recV[ra]);
}

generated quantities {
    // compute log_lik for WAIC and friends
    real log_lik [J];
    // Simulate a user + their recommendation output proportions
    real nThetaP;
    real<lower=0, upper=1> thetaP;
    int<lower=5> nP = 0;
    int<lower=0> yP;

    vector[A] biasP;
    vector[A] noiseP;
    vector[A] thetaRP;

    nThetaP = normal_rng(mu, sigma);
    thetaP = inv_logit(nThetaP);
    nP = neg_binomial_2_rng(nMean, nDisp) + 5;
    yP = binomial_rng(nP, thetaP);

    biasP = recB + recS * nThetaP;
    for (a in 1:A) {
        noiseP[a] = normal_rng(0, recV[a]);
    }
    thetaRP = inv_logit(noiseP + biasP);

    // accumulate profile log_lik
    for (i in 1:J) {
        log_lik[i] = binomial_lpmf(y[i] | n[i], theta[i]) + neg_binomial_2_lpmf(shiftN[i] | nMean, nDisp);
    }
    // accumulate list log_lik
    for (i in 1:NL) {
        log_lik[ru[i]] += normal_lpdf(rll[i] | recB[ra[i]] + recS[ra[i]] .* nTheta[ru[i]], recV[ra[i]]);
    }
}
