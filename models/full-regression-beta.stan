data {
    // The number of algorithms
    int<lower=0> A;
    // The number of data points
    int<lower=0> J;
    // The number of user,rec pairs
    int<lower=0> NL;
    // The user profile sizes
    int<lower=0> n[J];
    // The user profile female author counts
    int<lower=0> y[J];
    // The user rec list users
    int<lower=0> ru[NL];
    // The user rec list algorithms
    int<lower=0> ra[NL];
    // The user rec list sizes
    int<lower=0> rn[NL];
    // The user rec list female author counts
    int<lower=0> ry[NL];
}
parameters {
    // user profile distribution parameters
    real<lower=0,upper=1> phi;
    real<lower=0> lambda;
    real<lower=0> nMu;
    real<lower=0> nDisp;

    // recommender intercepts
    vector[A] recB;
    // recommender slopes
    vector[A] recS;
    // recommender variances
    vector<lower=0>[A] recC;

    // user profile biases
    vector<lower=0,upper=1>[J] theta;
    // recommender profile biases
    vector<lower=0,upper=1>[NL] thetaR;
}
transformed parameters {
    // user profile distribution parameters
    real<lower=0> alpha;
    real<lower=0> beta;

    // recommender profile mean bias
    vector<lower=0,upper=1>[NL] rlPhi;
    vector<lower=0>[NL] rlAlpha;
    vector<lower=0>[NL] rlBeta;
    
    alpha = lambda * phi;
    beta = lambda * (1 - phi);

    // RL bias is a function of user bias
    rlPhi = inv_logit(recB[ra] + recS[ra] .* logit(theta[ru]));
    rlAlpha = recC[ra] .* rlPhi;
    rlBeta = recC[ra] .* (1 - rlPhi);
}
model {
    // priors for user profile distribution
    phi ~ beta(1,1);
    lambda ~ lognormal(0, 5);

    nMu ~ lognormal(0, 5);
    nDisp ~ lognormal(0, 5);

    // priors for recommender parameters
    recB ~ normal(0, 10);
    recS ~ normal(0, 10);
    recC ~ lognormal(0, 5);

    // model user profile
    theta ~ beta(alpha, beta);
    n ~ neg_binomial_2(nMu, nDisp);
    y ~ binomial(n, theta);

    // model recommendation lists
    thetaR ~ beta(rlAlpha, rlBeta);
    ry ~ binomial(rn, thetaR);
}
/* generated quantities {
    real thetaP;
    int<lower=0> nP;
    int<lower=0> yP;

    vector<lower=0>[A] phiRP;
    vector<lower=0>[A] alphaRP;
    vector<lower=0>[A] betaRP;
    vector<lower=0,upper=1>[A] thetaRP;
    int yRP[A];
    
    thetaP = beta_rng(alpha, beta);
    nP = neg_binomial_2_rng(nMu, nDisp);
    yP = binomial_rng(nP, thetaP);

    for (i in 1:A) {
        phiRP[i] = inv_logit(recB[i] + recS[i] * logit(thetaP));
        alphaRP[i] = phiRP[i] * recC[i];
        betaRP[i] = (1 - phiRP[i]) * recC[i];
        thetaRP[i] = beta_rng(alphaRP[i], betaRP[i]);
        yRP[i] = binomial_rng(50, thetaRP[i]);
    }
} */
