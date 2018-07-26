import org.grouplens.lenskit.transform.threshold.RealThreshold
import org.grouplens.lenskit.transform.threshold.Threshold
import org.lenskit.api.ItemScorer
import org.lenskit.data.entities.CommonTypes
import org.lenskit.data.ratings.EntityCountRatingVectorPDAO
import org.lenskit.data.ratings.InteractionEntityType
import org.lenskit.data.ratings.RatingVectorPDAO
import org.lenskit.knn.NeighborhoodSize
import org.lenskit.knn.item.ItemItemScorer
import org.lenskit.knn.item.ItemSimilarityThreshold
import org.lenskit.knn.item.NeighborhoodScorer
import org.lenskit.knn.item.SimilaritySumNeighborhoodScorer

bind ItemScorer to ItemItemScorer

bind RatingVectorPDAO to EntityCountRatingVectorPDAO
set InteractionEntityType to CommonTypes.RATING
bind NeighborhoodScorer to SimilaritySumNeighborhoodScorer
bind (ItemSimilarityThreshold, Threshold) to RealThreshold

set NeighborhoodSize to 30