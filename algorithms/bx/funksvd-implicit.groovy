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

set FeatureCount to 55