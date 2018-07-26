import org.grouplens.lenskit.transform.threshold.RealThreshold
import org.grouplens.lenskit.transform.threshold.Threshold
import org.lenskit.api.ItemScorer
import org.lenskit.data.entities.CommonTypes
import org.lenskit.data.ratings.EntityCountRatingVectorPDAO
import org.lenskit.data.ratings.InteractionEntityType
import org.lenskit.data.ratings.RatingVectorPDAO
import org.lenskit.knn.NeighborhoodSize
import org.lenskit.knn.user.*
import org.lenskit.similarity.CosineVectorSimilarity
import org.lenskit.similarity.VectorSimilarity

bind ItemScorer to UserUserItemScorer
bind NeighborFinder to SnapshotNeighborFinder

within(UserSimilarity) {
    bind VectorSimilarity to CosineVectorSimilarity
}

bind RatingVectorPDAO to EntityCountRatingVectorPDAO
set InteractionEntityType to CommonTypes.RATING
bind UserNeighborhoodScorer to SimilaritySumUserNeighborhoodScorer
bind (UserSimilarityThreshold, Threshold) to RealThreshold

set NeighborhoodSize to 5