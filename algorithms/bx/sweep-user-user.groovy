import org.grouplens.lenskit.transform.threshold.RealThreshold
import org.grouplens.lenskit.transform.threshold.Threshold
import org.lenskit.api.ItemScorer
import org.lenskit.baseline.BaselineScorer
import org.lenskit.bias.BiasDamping
import org.lenskit.bias.BiasItemScorer
import org.lenskit.bias.BiasModel
import org.lenskit.bias.UserItemBiasModel
import org.lenskit.knn.MinNeighbors
import org.lenskit.knn.NeighborhoodSize
import org.lenskit.knn.user.*
import org.lenskit.similarity.CosineVectorSimilarity
import org.lenskit.similarity.VectorSimilarity
import org.lenskit.transform.normalize.MeanCenteringVectorNormalizer
import org.lenskit.transform.normalize.UserVectorNormalizer
import org.lenskit.transform.normalize.VectorNormalizer

bind ItemScorer to UserUserItemScorer
bind(BaselineScorer, ItemScorer) to BiasItemScorer
bind BiasModel to UserItemBiasModel
bind (UserSimilarityThreshold, Threshold) to RealThreshold
set BiasDamping to 7.0

bind NeighborFinder to SnapshotNeighborFinder

within (UserVectorNormalizer) {
    bind VectorNormalizer to MeanCenteringVectorNormalizer
}

within(UserSimilarity) {
    bind VectorSimilarity to CosineVectorSimilarity
}

for (k in [5,10,15,20,25,30,35,40,45,50]) {
    algorithm("UserUser") {
        attributes["NNbrs"] = k
        set NeighborhoodSize to k
    }
    algorithm("UserUserL") {
        attributes["NNbrs"] = k
        set NeighborhoodSize to k
        set MinNeighbors to 2
    }
}
