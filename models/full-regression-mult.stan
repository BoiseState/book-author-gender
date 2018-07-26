functions {
    real mult_binomial_lpmf(int[] y, int[] n, vector theta, vector psi) {
        int sz = size(y);
        real result;
        vector[sz] ltheta;
        vector[sz] l1mtheta;
        
        if (size(n) != sz) {
            reject("n and y have different sizes");
        }
        if (rows(theta) != sz) {
            reject("theta and y have different sizes");
        }
        if (rows(psi) != sz) {
            reject("psi and y have different sizes");
        }
        
        ltheta = log(theta);
        l1mtheta = log1m(theta);

        // underlyng binomial
        result = binomial_lpmf(y | n, theta);
        // add multiplicative factor
        for (i in 1:sz) {
            if (psi[i] >= 1.0e-6) {
                result = result + psi[i] * y[i] * (n[i] - y[i]);
            }
        }
        
        // compute scaling factors
        for (i in 1:sz) {
            real thisPsi = psi[i];
            int thisN = n[i];
            real prob = 0;
            
            if (thisPsi < 1.0e-6) {
                continue;
            }
            
            for (yj in 0:thisN) {
                real ll;
                ll = lchoose(thisN, yj);
                ll = ll + yj * ltheta[i];
                ll = ll + l1mtheta[i] * (thisN - yj);
                ll = ll + thisPsi * yj * (thisN - yj);
                prob = prob + exp(ll);
            }
            
            result = result - log(prob);
        }

        return result;
    }
}
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
    // recommender underdispersions
    vector<lower=0,upper=1>[A] recU;

    // user profile biases
    vector[J] lgThetaErr;
    // rec profile errors
    vector[NL] lgThetaErrR;
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
    theta = inv_logit(mu + lgThetaErr * sigma);
    thetaR = inv_logit(recBias + lgThetaErrR * recV[ra]);
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
    recU ~ exponential(2);

    // model user profile
    n ~ neg_binomial_2(nMu, nDisp);
    lgThetaErr ~ normal(0, 1);
    y ~ binomial(n, theta);

    // model recommendation lists
    lgThetaErrR ~ normal(0, 1);
    ry ~ mult_binomial(rn, thetaR, recU[ra]);
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
