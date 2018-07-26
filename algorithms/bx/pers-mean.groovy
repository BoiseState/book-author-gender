import org.lenskit.api.ItemScorer
import org.lenskit.bias.BiasDamping
import org.lenskit.bias.BiasItemScorer
import org.lenskit.bias.BiasModel
import org.lenskit.bias.UserItemBiasModel

bind ItemScorer to BiasItemScorer
bind BiasModel to UserItemBiasModel
set BiasDamping to 5.0d