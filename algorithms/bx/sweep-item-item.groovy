import org.grouplens.lenskit.transform.threshold.RealThreshold
import org.grouplens.lenskit.transform.threshold.Threshold
import org.lenskit.api.ItemScorer
import org.lenskit.baseline.BaselineScorer
import org.lenskit.bias.*
import org.lenskit.knn.MinNeighbors
import org.lenskit.knn.NeighborhoodSize
import org.lenskit.knn.item.ItemItemScorer
import org.lenskit.knn.item.ItemSimilarityThreshold
import org.lenskit.transform.normalize.BiasUserVectorNormalizer
import org.lenskit.transform.normalize.UserVectorNormalizer

bind ItemScorer to ItemItemScorer
bind UserVectorNormalizer to BiasUserVectorNormalizer
within(UserVectorNormalizer) {
    bind BiasModel to ItemBiasModel
}
set BiasDamping to 7.0

bind(BaselineScorer, ItemScorer) to BiasItemScorer
bind BiasModel to UserItemBiasModel

bind (ItemSimilarityThreshold, Threshold) to RealThreshold

for (k in [5,10,15,20,25,30,35,40,45,50]) {
    algorithm("ItemItem") {
        attributes["NNbrs"] = k
        set NeighborhoodSize to k
    }
    algorithm("ItemItemL") {
        attributes["NNbrs"] = k
        set NeighborhoodSize to k
        set MinNeighbors to 2
    }
}