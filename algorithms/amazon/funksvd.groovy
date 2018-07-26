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
set FeatureCount to 25
set IterationCount to 125
