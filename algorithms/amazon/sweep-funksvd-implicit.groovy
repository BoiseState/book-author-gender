import org.grouplens.lenskit.iterative.IterationCount
import org.lenskit.api.ItemScorer
import org.lenskit.baseline.BaselineScorer
import org.lenskit.bias.BiasDamping
import org.lenskit.bias.BiasItemScorer
import org.lenskit.bias.BiasModel
import org.lenskit.bias.GlobalBiasModel
import org.lenskit.bias.UserItemBiasModel
import org.lenskit.data.entities.CommonTypes
import org.lenskit.data.ratings.EntityCountRatingVectorPDAO
import org.lenskit.data.ratings.InteractionEntityType
import org.lenskit.data.ratings.RatingVectorPDAO
import org.lenskit.mf.funksvd.FeatureCount
import org.lenskit.mf.funksvd.FunkSVDItemScorer

bind BiasModel to new GlobalBiasModel(0.0d)

bind ItemScorer to FunkSVDItemScorer
set IterationCount to 125

bind RatingVectorPDAO to EntityCountRatingVectorPDAO
set InteractionEntityType to CommonTypes.RATING

for (k in [5,10,15,20,25,30,35,40,45,50,60,70,80,90,100]) {
    algorithm("FunkSVD") {
        attributes["FeatureCount"] = k
        set FeatureCount to k
    }
}