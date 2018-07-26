import org.grouplens.lenskit.transform.threshold.RealThreshold
import org.grouplens.lenskit.transform.threshold.Threshold
import org.lenskit.api.ItemScorer
import org.lenskit.data.entities.CommonTypes
import org.lenskit.data.ratings.EntityCountRatingVectorPDAO
import org.lenskit.data.ratings.InteractionEntityType
import org.lenskit.data.ratings.RatingVectorPDAO
import org.lenskit.knn.NeighborhoodSize
import org.lenskit.knn.item.ItemItemScorer
import org.lenskit.knn.item.NeighborhoodScorer
import org.lenskit.knn.item.SimilaritySumNeighborhoodScorer
import org.lenskit.knn.user.UserSimilarityThreshold

bind ItemScorer to ItemItemScorer

bind RatingVectorPDAO to EntityCountRatingVectorPDAO
set InteractionEntityType to CommonTypes.RATING
bind NeighborhoodScorer to SimilaritySumNeighborhoodScorer
bind (UserSimilarityThreshold, Threshold) to RealThreshold

for (k in [5,10,15,20,25,30,35,40,45,50,60,70,80,90,100]) {
    algorithm("ItemItem") {
        attributes["NNbrs"] = k
        set NeighborhoodSize to k
    }
}
