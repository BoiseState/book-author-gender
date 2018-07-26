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
import org.lenskit.data.entities.CommonTypes
import org.lenskit.data.ratings.EntityCountRatingVectorPDAO
import org.lenskit.data.ratings.InteractionEntityType
import org.lenskit.data.ratings.RatingVectorPDAO

bind ItemScorer to HPFItemScorer

//bind HPFModel toProvider HPFModelProvider
set StoppingThreshold to 0.000001
set IsProbabilityPrediction to false
set ConvergenceCheckFrequency to 10
set IterationCount to 300
set ItemActivityPriorShp to 0.5
set ItemWeightPriorShp to 0.5
set UserActivityPriorShp to 0.5
set UserWeightPriorShp to 0.5

set RandomSeed to System.currentTimeMillis()

for (k in [5,10,15,20,25,30,35,40,45,50,60,70,80,90,100]) {
//	for (a in [0.5]){
//		for (b in [0.5]){
		algorithm("PF") {
        	attributes["FeatureCount"] = k
        	set FeatureCount to k
//		attributes["ItemActivity"] = a
//		set ItemActivityShpPrior to a
//		set ItemWeightShpPrior to a
//		attributes["UserActivity"] = b
//		set UserActivityShpPrior to b
//		set UserWeightShpPrior to b
//		attributes["ActivityPriorMean"] = b
//		set UserActivityPriorMean to b
//		set ItemActivityPriorMean to b
//			}
//		}
    	}
}
