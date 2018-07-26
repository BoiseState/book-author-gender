import org.grouplens.lenskit.transform.threshold.RealThreshold
import org.grouplens.lenskit.transform.threshold.Threshold
import org.lenskit.api.ItemScorer
import org.lenskit.baseline.BaselineScorer
import org.lenskit.bias.*
import org.lenskit.knn.NeighborhoodSize
import org.lenskit.knn.item.ItemItemScorer
import org.lenskit.knn.item.ItemSimilarityThreshold
import org.lenskit.knn.item.MinCommonUsers
import org.lenskit.knn.item.ModelSize
import org.lenskit.transform.normalize.BiasUserVectorNormalizer
import org.lenskit.transform.normalize.UserVectorNormalizer

bind ItemScorer to ItemItemScorer
bind UserVectorNormalizer to BiasUserVectorNormalizer
within(UserVectorNormalizer) {
    bind BiasModel to ItemBiasModel
}

bind(BaselineScorer, ItemScorer) to BiasItemScorer
bind BiasModel to UserItemBiasModel
set BiasDamping to 5.0d
bind (ItemSimilarityThreshold, Threshold) to RealThreshold

set NeighborhoodSize to 20
set ModelSize to 10000
set MinCommonUsers to 2
