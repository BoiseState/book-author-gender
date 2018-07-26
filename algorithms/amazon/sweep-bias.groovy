import org.lenskit.api.ItemScorer
import org.lenskit.bias.BiasDamping
import org.lenskit.bias.BiasItemScorer
import org.lenskit.bias.BiasModel
import org.lenskit.bias.UserItemBiasModel

bind ItemScorer to BiasItemScorer
bind BiasModel to UserItemBiasModel

for (k in 1..100) {
    algorithm("Bias") {
        attributes["Damping"] = k
        set BiasDamping to k
    }
}