---
header-includes:
- |
  \usepackage{tikz}
  \usetikzlibrary{bayesnet}
---

# Modeling Profiles and Recommendation List

## Modeling the Profile

We model user profiles with a hierarchical model summarized below:

\begin{figure}
  \centering
  \tikz{ %
    \node[latent] (theta) {$\theta$} ; %
    \node[obs, right=of theta] (y) {$y_j$} ; %
    \node[obs, above=of y] (n) {$n_j$} ; %
    \node[const, above left=of n] (nu) {$\nu$} ;
    \node[const, above right=of n] (gamma) {$\gamma$};
    \node[const, above left=of theta] (mu) {$\mu$};
    \node[const, below left=of theta] (sigma) {$\sigma$};
    \plate[inner sep=0.25cm, xshift=-0.12cm, yshift=0.12cm] {plate1} {(theta) (y) (n)} {$j \in U$}; %
    \edge {theta} {y} ; %
    \edge {n} {y} ; %
    \edge {nu} {n} ;
    \edge {gamma} {n} ;
    \edge {mu} {theta};
    \edge {sigma} {theta};
  }
\end{figure}

### Input Data

Each user has a profile; all we need is the (known-gender) profile size ($n_j$) and the number of female authors ($y_j$).  `J` is the number of users.

!lit(@profile_data)(stan)
~~~~
int<lower=0> J;
int<lower=5> n[J];
int<lower=0> y[J];
~~~~

The smallest profile size is 5, by experimental design; therefore, want a shifted profile data piece.

!lit(@profile_xdata)(stan)
~~~~
int<lower=0> shiftN[J];
~~~~

!lit(@profile_data_transforms)(stan)
~~~~
for (i in 1:J) {
    shiftN[i] = n[i] - 5;
}
~~~~

### Modeling Profile Sizes

In order to realistically do predictive modeling, our model must model user profile sizes as being drawn from a distribution. A Poisson distribution has too much (and uncontrollable) variance, so we will use a negative binomial with mean $\nu$ and dispersion $\gamma$.  Further, since we have a minimum size of 5, we will apply the distribution to the shifted values.

We tested several different ways of modeling profile sizes, and a negative binomial on shifted sizes had the best fit.  This means that $\nu$ will not quite be the true mean.

Parameter definitions:

!lit(@profile_params)(stan)
~~~
real<lower=0> nMean;
real<lower=0> nDisp;
~~~

And the likelihood model:

!lit(@profile_model)(stan)
~~~
shiftN ~ neg_binomial_2(nMean, nDisp);
~~~

We'll place a vague prior on both the mean and dispersion.

!lit(@profile_prior)(stan)
~~~
nMean ~ exponential(0.001);
nDisp ~ exponential(0.001);
~~~

### Modeling Profile Observations

Following a hierarchical model, each user has a profile bias $\theta_j$. We model the observed author distribution with a binomial:

$$y_j \sim \mathrm{Binomial}(n_j, \theta_j)$$

!lit(@profile_model)(stan)
~~~~
y ~ binomial(n, theta);
~~~~

### Modeling Profile Bias

The common way to model the distribution of $\theta_j$ is with a Beta distribution, as in Gelman. However, a logit-normal is more computationally efficient, and will be more conceptually consistent when we go to do a regression.  Also, we tested both a beta model and a logit-normal model, and found the logit-normal model to have moderately better fit.

Therefore, we will model bias as the logit transform of a normal variable with parameters $\mu$ and $\sigma^2$:

$$\begin{aligned}
\theta'_j & = \mathrm{logit}(\theta_j) \\
\theta'_j & \sim \mathrm{Normal}(\mu, \sigma)
\end{aligned}$$

So we define our parameters;

!lit(@profile_params)(stan)
~~~~
real mu;
real<lower=0> sigma;
vector[J] nTheta;
~~~~

Some transformed parameters:

!lit(@profile_xparams)(stan)
~~~~
vector<lower=0,upper=1>[J] theta;
~~~~

Their transformation:

!lit(@profile_transforms)(stan)
~~~~
theta = inv_logit(nTheta);
~~~~

And then a likelihood model:

!lit(@profile_model)(stan)
~~~~
nTheta ~ normal(mu, sigma);
~~~~

Finally, we will place vague priors over $\mu$ and $\sigma$:

!lit(@profile_prior)(stan)
~~~~
mu ~ normal(0, 100);
sigma ~ exponential(0.001);
~~~~

### Generating Predictions

Finally, in order to compare posterior predictions with observed data, we want to draw samples from the fitted model. We can do this along with the fitting, with the following generator code.

!lit(@profile_predict_vars)(stan)
~~~~
real nThetaP;
real<lower=0, upper=1> thetaP;
int<lower=5> nP = 0;
int<lower=0> yP;
~~~~

!lit(@profile_predict_model)(stan)
~~~~
nThetaP = normal_rng(mu, sigma);
thetaP = inv_logit(nThetaP);
nP = neg_binomial_2_rng(nMean, nDisp) + 5;
yP = binomial_rng(nP, thetaP);
~~~~

### The Model

For diagnostic purposes, we want to fit just the profiles, before we try to fit the recommendation lists too.

!lit(profile.stan)(stan)
~~~~
// This file is generated from models.md
data {
    @profile_data
}
transformed data {
    @profile_xdata
    @profile_data_transforms
}
parameters {
    @profile_params
}
transformed parameters {
    @profile_xparams
    @profile_transforms
}
model {
    // prior distribution
    @profile_prior
    // likelihood model
    @profile_model
}
generated quantities {
    @profile_predict_vars
    @profile_predict_model
}
~~~~

## Recommendation Lists

![Plate diagram for profile and recommendation lists](reclist-plate-1.pdf)

### Input Data

We need a way to represent recommendation lists in the system. I would prefer to use a matrix; however, not every user has recommendations from every algorithm, so it would be an incomplete matrix; Stan does not like incomplete data.

Therefore we represent each list as a data point, and include its algorithm.

We need the sizes - the number of algorithms and lists:

!lit(@list_data)(stan)
~~~~
int<lower=0> A;
int<lower=0> NL;
~~~~

And we need the data itself - the recommender user $\bar u_i$ (`ru`), the recommender algorithm $\bar a_i$ (`ra`), the recommendation (known author) list size $\bar n_i$ (`rn`), and the number of female authors $\bar y_i$ (`ry`).

!lit(@list_data)(stan)
~~~~
int<lower=1,upper=J> ru[NL];
int<lower=1,upper=A> ra[NL];
int<lower=0> rn[NL];
int<lower=0> ry[NL];
~~~~

We also want the observed proportion of female authors.

!lit(@list_xdata)(stan)
~~~
vector<lower=0,upper=1>[NL] rp;
vector[NL] rll;
~~~

!lit(@list_data_transforms)(stan)
~~~
rp = (to_vector(ry) + 1) ./ (to_vector(rn) + 2);
rll = logit(rp);
~~~

### Modeling Recommender Response

Again, we will use a binomial to model the distribution of observed female proportions in recommender output lists, such that:

$$\begin{aligned}
\bar y_i & \sim \mathrm{Binomial}(\bar n_i, \bar \theta_{i}) \\
\bar\theta'_i & = \mathrm{logit}(\bar\theta_i)
\end{aligned}$$

We want to just write this:

!lit(@list_modelskip)(stan)
~~~~
ry ~ binomial(rn, thetaR);
~~~~

However, due to our consistency accomodation, we can't. See the next section for details on that.

The key to relating recommender output to user profile properties is through a linear regression in the logit space, the space in which user biases are taken to be normally distributed.  We do this relation in terms of a recommender baseline bias $b_a$, response slope $s_a$, and variance $\sigma^2_a$.  This is defined by:

$$\begin{aligned}
\bar \theta'_i & = b_a + s_a \theta'_{u_i} + \epsilon_i \\
\epsilon_i & \sim \mathrm{Normal}(0, \sigma_a)
\end{aligned}$$

So we need a noise parameter:

!lit(@list_xparams)(stan)
~~~~
vector[NL] rbias;
vector[NL] noiseR;
~~~~

And our recommender response parameters:

!lit(@list_params)(stan)
~~~~
vector[A] recB;
vector[A] recS;
vector<lower=0>[A] recV;
~~~~

And then we need to connect these to the user profile $\theta$s and the recommender properties.

!lit(@list_transforms)(stan)
~~~~
rbias = recB[ra] + recS[ra] .* nTheta[ru];
noiseR = rll - rbias;
~~~~

Noise is normal:

!lit(@list_model)(stan)
~~~~
noiseR ~ normal(0, recV[ra]);
~~~~

And finally we put vague priors on our recommender response parameters.  These will be vague.

!lit(@list_priors)(stan)
~~~~
recB ~ normal(0, 100);
recS ~ normal(0, 100);
recV ~ exponential(0.001);
~~~~

### Predicting Lists

We now want to draw a synthetic user, so that we can examine posterior predictive distributions.  We have already written the code to do this for a new user; we now generate their lists.

!lit(@list_predict_vars)(stan)
~~~~
vector[A] biasP;
vector[A] noiseP;
vector[A] thetaRP;
~~~~

!lit(@list_predict_model)(stan)
~~~~
biasP = recB + recS * nThetaP;
for (a in 1:A) {
    noiseP[a] = normal_rng(0, recV[a]);
}
thetaRP = inv_logit(noiseP + biasP);
~~~~

### The Model

Now we want to put all of this together into a model.

!lit(full.stan)(stan)
~~~~
// This file is generated from models.md
data {
    @profile_data
    @list_data
}
transformed data {
    @profile_xdata
    @list_xdata
    @profile_data_transforms
    @list_data_transforms
}
parameters {
    @profile_params
    @list_params
}
transformed parameters {
    @profile_xparams
    @list_xparams
    @profile_transforms
    @list_transforms
}
model {
    // profile prior distribution
    @profile_prior
    // rec list priors
    @list_priors

    // profile likelihood model
    @profile_model
    
    // rec list likelihood model
    @list_model
}
generated quantities {
    @profile_predict_vars
    @list_predict_vars
    @profile_predict_model
    @list_predict_model
}
~~~~
