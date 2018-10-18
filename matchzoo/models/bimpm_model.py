"""Naive model with a simplest structure for testing purposes."""

from keras.models import Model
from keras.layers import Input, Bidirectional, LSTM, Dense, Concatenate


from matchzoo import engine
from matchzoo.layers import MultiPerspectiveLayer


class BimpmModel(engine.BaseModel):
    """Naive model with a simplest structure for testing purposes."""

    @classmethod
    def get_default_params(cls) -> engine.ParamTable:
        """:return: model default parameters."""
        params = super().get_default_params()
        params['optimizer'] = 'adam'
        params['input_shapes'] = [(32,), (32,)]
        params.add(engine.Param('w_initializer', 'glorot_uniform'))
        params.add(engine.Param('b_initializer', 'zeros'))
        params.add(engine.Param('activation_hidden', 'linear'))
        params.add(engine.Param('dim_hidden', 128))
        params.add(engine.Param('strategy', {'full': True,
                                             'max-pooling': True,
                                             'attentive': True,
                                             'max-attentive': True}))
        return params

    def build(self):
        """Build."""
        # Word representation layer.
        # TODO Concanate word level embedding and character level embedding.
        # Word level- pre trained.
        # Character level not pre trained.
        input_shape_lt = self._params['input_shapes'][0]
        input_shape_rt = self._params['input_shapes'][1]
        input_lt = Input(shape=input_shape_lt)
        input_rt = Input(shape=input_shape_rt)
        # Context represntation layer.
        x_lt = Bidirectional(LSTM(input_shape_lt[0],
                                  return_sequences=True,
                                  kernel_initializer=self._params['w_initializer'],
                                  bias_initializer=self._params['b_initializer']),
                             merge_mode=None)(input_lt)
        x_rt = Bidirectional(LSTM(input_shape_rt[0],
                                  return_sequences=True,
                                  kernel_initializer=self._params['w_initializer'],
                                  bias_initializer=self._params['b_initializer']),
                             merge_mode=None)(input_rt)
        # Multiperspective Matching layer.
        # Output is two sequence of vectors.
        # TODO Finalize MultiPerspectiveMatching
        x_lt, x_rt = MultiPerspectiveLayer(output_dim=10,
                                           strategy=self._params['strategy'])([x_lt, x_rt])
        # Aggregation layer.
        x_lt = Bidirectional(LSTM(self._params['dim_hidden'],
                                  return_sequences=False,
                                  kernel_initializer=self._params['w_initializer'],
                                  bias_initializer=self._params['b_initializer']),
                             merge_mode='concat')(x_lt)
        x_rt = Bidirectional(LSTM(self._params['dim_hidden'],
                                  return_sequences=False,
                                  kernel_initializer=self._params['w_initializer'],
                                  bias_initializer=self._params['b_initializer']),
                             merge_mode='concat')(x_lt)
        # catenate the forward-backward vector of left & right (only last step).
        # Concatenate the concatenated vector of left and right.
        x = Concatenate()([x_lt, x_rt])
        # prediction layer.
        x = Dense(self._params['dim_hidden'],
                  activation=self._params['activation_hidden'])(x)
        x = Dense(self._params['dim_hidden'],
                  activation=self._params['activation_hidden'])(x)
        x_out = self._make_output_layer()(x)
        self._backend = Model(
            inputs=[input_lt, input_rt],
            outputs=x_out)