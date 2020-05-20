import numpy as np
from agents.ValueSim import ValueSim
from agents.cppmodule.core import get_all_childs, select_trace_obs, backup_trace_obs_LP
from agents.cppmodule.core import get_unique_child_obs


class ValueSimLP(ValueSim):

    def __init__(self, **kwargs):

        super().__init__(min_visits_to_store=5, **kwargs)

    def evaluate_states(self, states):

        v, var = self.model.inference(states[:, None, :, :])

        return np.squeeze(v, axis=1), np.squeeze(var, axis=1)

    def mcts(self, root_index, sims):

        child = self.arrays['child']
        score = self.arrays['score']
        games = self.game_arr
        eval_ = self.evaluate_states

        if self.projection:
            state = self.obs_arrays['state']
            visit = self.obs_arrays['visit']
            value = self.obs_arrays['value']
            variance = self.obs_arrays['variance']
            end = self.arrays['end']
            n_to_o = self.node_to_obs
            s_args = [root_index, child, visit, value, variance, score, n_to_o, 1]
            selection = select_trace_obs
            b_args = [
                None, visit, value, variance, n_to_o, score,
                end, None, None, None, None, self.gamma]
            #backup = backup_trace_mixture_obs
            backup = backup_trace_obs_LP
        else:
            visit = self.arrays['visit']
            value = self.arrays['value']
            variance = self.arrays['variance']
            s_args = [root_index, child, visit, value, variance, score]
            selection = select_trace
            b_args = [None, visit, value, variance, score, None, None, self.gamma]
            backup = backup_trace

        for i in range(sims):
            trace = selection(*s_args)

            leaf_index = trace[-1]

            leaf_game = games[leaf_index]

            if not leaf_game.end:

                self.expand(leaf_game)

                _c, _o = get_unique_child_obs(leaf_index, child, score, n_to_o)

                states = state[_o]

                v, var = eval_(states)
            else:
                _c = _o = []
                v = var = np.empty(0, dtype=np.float32)

            b_args[0] = trace
            b_args[-5] = _c
            b_args[-4] = _o
            b_args[-3] = v
            b_args[-2] = var
            backup(*b_args)
            #print(i, visit[n_to_o[self.root]], value[n_to_o[self.root]], variance[n_to_o[self.root]])
            #input()
