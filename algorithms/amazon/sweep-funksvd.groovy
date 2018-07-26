import org.grouplens.lenskit.iterative.IterationCount
import org.lenskit.api.ItemScorer
import org.lenskit.baseline.BaselineScorer
import org.lenskit.bias.BiasDamping
import org.lenskit.bias.BiasItemScorer
import org.lenskit.bias.BiasModel
import org.lenskit.bias.UserItemBiasModel
import org.lenskit.mf.funksvd.FeatureCount
import org.lenskit.mf.funksvd.FunkSVDItemScorer

bind(BaselineScorer, ItemScorer) to BiasItemScorer
bind BiasModel to UserItemBiasModel
set BiasDamping to 5.0d

bind ItemScorer to FunkSVDItemScorer
set IterationCount to 125

for (k in [5,10,15,20,25,30,35,40,45,50,60,70,80,90,100]) {
    algorithm("FunkSVD") {
        attributes["FeatureCount"] = k
        set FeatureCount to k
    }
}
