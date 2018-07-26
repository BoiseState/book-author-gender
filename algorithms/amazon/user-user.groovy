import org.grouplens.lenskit.transform.threshold.RealThreshold
import org.grouplens.lenskit.transform.threshold.Threshold
import org.lenskit.api.ItemScorer
import org.lenskit.baseline.BaselineScorer
import org.lenskit.bias.BiasDamping
import org.lenskit.bias.BiasItemScorer
import org.lenskit.bias.BiasModel
import org.lenskit.bias.UserItemBiasModel
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
set BiasDamping to 5.0d
bind (UserSimilarityThreshold, Threshold) to RealThreshold

bind NeighborFinder to SnapshotNeighborFinder

within (UserVectorNormalizer) {
    bind VectorNormalizer to MeanCenteringVectorNormalizer
}

within(UserSimilarity) {
    bind VectorSimilarity to CosineVectorSimilarity
}

set NeighborhoodSize to 30
