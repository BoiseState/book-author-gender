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
    real mu;
    real<lower=0> sigma;
    real<lower=0> nMu;
    real<lower=0> nDisp;

    // recommender intercepts
    vector[A] recB;
    // recommender slopes
    vector[A] recS;
    // recommender variances
    vector<lower=0>[A] recV;

    // user profile biases
    vector[J] lgTheta;
    // recommender profile biases
    vector[NL] lgThetaR;
}
transformed parameters {
    // transformed profile bias
    vector<lower=0,upper=1>[J] theta;

    // transformed recommender profile bias
    vector<lower=0,upper=1>[NL] thetaR;
    
    // estimated recommender profile bias
    vector[NL] recBias;
    
    // RL bias is a function of user bias
    recBias = recB[ra] + recS[ra] .* lgTheta[ru];
    
    // Thetas are inv logit of lg thetas
    theta = inv_logit(lgTheta);
    thetaR = inv_logit(lgThetaR);
}
model {
    // priors for user profile distribution
    mu ~ normal(0, 100);
    sigma ~ normal(0, 10);

    nMu ~ lognormal(0, 5);
    nDisp ~ lognormal(0, 5);
    
    // priors for recommender parameters
    recB ~ normal(0, 10);
    recS ~ normal(0, 10);
    recV ~ normal(0, 10);

    // model user profile
    n ~ neg_binomial_2(nMu, nDisp);
    lgTheta ~ normal(mu, sigma);
    y ~ binomial(n, theta);

    // model recommendation lists
    lgThetaR ~ normal(recBias, recV[ra]);
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
