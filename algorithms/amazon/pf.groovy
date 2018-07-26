import org.grouplens.lenskit.iterative.IterationCount
import org.grouplens.lenskit.iterative.StoppingThreshold

import org.lenskit.api.ItemScorer

import org.lenskit.mf.funksvd.FeatureCount

import org.lenskit.pf.HPFItemScorer
import org.lenskit.pf.IsProbabilityPrediction
import org.lenskit.pf.ConvergenceCheckFrequency
import org.lenskit.pf.RandomSeed
import org.lenskit.pf.ItemActivityPriorShp
import org.lenskit.pf.ItemWeightPriorShp
import org.lenskit.pf.UserActivityPriorShp
import org.lenskit.pf.UserWeightPriorShp
import org.lenskit.pf.ItemActivityPriorMean
import org.lenskit.pf.UserActivityPriorMean
import org.lenskit.pf.HPFModelProvider
import org.lenskit.pf.HPFModel

bind ItemScorer to HPFItemScorer

//bind HPFModel toProvider HPFModelProvider
set StoppingThreshold to 0.000001
set IsProbabilityPrediction to false
set ConvergenceCheckFrequency to 10
set IterationCount to 200
//set ItemActivityPriorShp to 0.5
//set ItemWeightPriorShp to 0.5
//set UserActivityPriorShp to 0.5
//set UserWeightPriorShp to 0.5
//set RandomSeed to System.currentTimeMillis()
set FeatureCount to 80
