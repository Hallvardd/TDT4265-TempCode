import numpy as np
import utils
import typing
np.random.seed(1)

def pre_process_images(X: np.ndarray, mean:float, std:float):
    """
    Args:
        X: images of shape [batch size, 784] in the range (0, 255)
    Returns:
        X: images of shape [batch size, 785] normalized as described in task2a
    """
    assert X.shape[1] == 784,\
        f"X.shape[1]: {X.shape[1]}, should be 784"

    # Input normalization
    X  = (X - mean)/std

    #bias trick after normalization
    X = np.insert(X, X.shape[1], 1, axis=1)
    # asd
    return X


def calculate_mean_and_std(X: np.ndarray) -> (float,float):

    mean = X.mean()
    std = X.std()

    return (mean, std)


def cross_entropy_loss(targets: np.ndarray, outputs: np.ndarray):
    """
    Args:
        targets: labels/targets of each image of shape: [batch size, num_classes]
        outputs: outputs of model of shape: [batch size, num_classes]
    Returns:
        Cross entropy error (float)
    """
    assert targets.shape == outputs.shape,\
        f"Targets shape: {targets.shape}, outputs: {outputs.shape}"

    x_loss = - np.sum(targets * np.log(outputs))/outputs.shape[0]
    return x_loss


class SoftmaxModel:

    def __init__(self,
                 # Number of neurons per layer
                 neurons_per_layer: typing.List[int],
                 use_improved_sigmoid: bool,  # Task 3a hyperparameter
                 use_improved_weight_init: bool  # Task 3c hyperparameter
                 ):
        # Always reset random seed before weight init to get comparable results.
        np.random.seed(1)
        # Define number of input nodes
        self.I = 785
        self.use_improved_sigmoid = use_improved_sigmoid
        self.use_improved_weight_init = use_improved_weight_init

        # Define number of output nodes
        # neurons_per_layer = [64, 10] indicates that we will have two layers:
        # A hidden layer with 64 neurons and a output layer with 10 neurons.
        self.neurons_per_layer = neurons_per_layer

        # Initialize the weights
        self.ws    = np.array([None for i in range(len(self.neurons_per_layer))])
        # Array for the different values used in the calculations
        self.z_arr = np.array([None for i in range(len(self.neurons_per_layer))])
        self.a_arr = np.array([None for i in range(len(self.neurons_per_layer))])
        self.delta = np.array([None for i in range(len(self.neurons_per_layer))])
        self.grads = np.array([None for i in range(len(self.neurons_per_layer))])

        prev = self.I
        for index,size in enumerate(self.neurons_per_layer):
            w_shape = (prev, size)
            print("Initializing weight to shape:", w_shape)
            w = np.zeros(w_shape)
            self.ws[index] = w
            prev = size


        # weight init
        self.fan_in_weights() if self.use_improved_weight_init else self.randomize_weigths()

        # activation functions
        #hidden layers
        self.f_hidden, self.f_prime_hidden = (self.imp_sigmoid, self.imp_sigmoid_d)\
        if self.use_improved_sigmoid else (self.sigmoid, self.sigmoid_d)
        #final layer
        self.f_final = self.softmax

    def forward(self, X: np.ndarray) -> np.ndarray:
        """
        Args:
            X: images of shape [batch size, 785]
        Returns:
            y: output of model with shape [batch size, num_outputs]
        """

        # first layer
        self.z_arr[0] = X @ self.ws[0]
        self.a_arr[0] = self.f_hidden(self.z_arr[0])

        #final layer
        self.z_arr[1] = self.a_arr[0] @ self.ws[1]
        self.a_arr[1] = self.f_final(self.z_arr[1])

        # output
        y = self.a_arr[1]

        return y

    def backward(self, X: np.ndarray, outputs: np.ndarray,
                 targets: np.ndarray) -> None:
        """
        Args:
            X: images of shape [batch size, 785]
            outputs: outputs of model of shape: [batch size, num_outputs]
            targets: labels/targets of each image of shape: [batch size, num_classes]
        """
        assert targets.shape == outputs.shape,\
            f"Output shape: {outputs.shape}, targets: {targets.shape}"

        # Softmax layer
        L = -1

        self.delta[L] = -(targets - outputs)
        self.grads[L] = (self.a_arr[L-1].T @ self.delta[L])/(X.shape[0])

        # first/last hidden layer
        L -= 1

        self.delta[L] = (self.delta[L+1] @ self.ws[L+1].T)*self.f_prime_hidden(self.z_arr[L])
        self.grads[L] = (X.T @ self.delta[L])/X.shape[0]

        for grad, w in zip(self.grads, self.ws):
            assert grad.shape == w.shape,\
                f"Expected the same shape. Grad shape: {grad.shape}, w: {w.shape}."

    # Activation functions
    def softmax(self, z:np.ndarray) -> np.ndarray:
        return  np.exp(z)/(np.sum(np.exp(z), axis=1, keepdims=True))

    def sigmoid(self, z:np.ndarray) -> np.ndarray:
        return 1.0/(1.0 + np.exp(-z))

    def sigmoid_d(self, z):
        return self.sigmoid(z)*(1-self.sigmoid(z))

    def imp_sigmoid(self, z):
        z_d = (2.0/3.0)*z
        return 1.7159 * np.tanh(z_d)

    def imp_sigmoid_d(self, z):
        z_d = (2.0/3.0)*z
        return (1.7159 * 8) / (3 * (np.exp(z_d) + np.exp(-z_d))**2)

    # Initialize weights funtions
    def randomize_weigths(self):
        for layer_idx, w in enumerate(self.ws):
            self.ws[layer_idx] = np.random.uniform(-1, 1, size=w.shape)

    def fan_in_weights(self):
        for layer_idx, w in enumerate(self.ws):
            self.ws[layer_idx] = np.random.normal(0, 1/(np.sqrt(w.shape[0])) ,size=w.shape)

    # Update weights
    def update_weights(self, learning_rate):
        self.ws -= self.grads*learning_rate

    def momentum_update_weights(self, learning_rate, momentum_grads):
        self.ws -= (self.grads + momentum_grads)*learning_rate

    def zero_grad(self) -> None:
        self.grads = [None for i in range(len(self.ws))]



def one_hot_encode(Y: np.ndarray, num_classes: int):
    """
    Args:
        Y: shape [Num examples, 1]
        num_classes: Number of classes to use for one-hot encoding
    Returns:
        Y: shape [Num examples, num classes]
    """
    # create an array of all zeros
    Y_hot = np.zeros((Y.shape[0], num_classes))
    # set the correct elements to one
    Y_hot[range(Y.shape[0]), Y.flatten()] = 1

    return Y_hot


def gradient_approximation_test(
        model: SoftmaxModel, X: np.ndarray, Y: np.ndarray):
    """
        Numerical approximation for gradients. Should not be edited.
        Details about this test is given in the appendix in the assignment.
    """
    epsilon = 1e-3
    for layer_idx, w in enumerate(model.ws):
        for i in range(w.shape[0]):
            for j in range(w.shape[1]):
                orig = model.ws[layer_idx][i, j].copy()
                model.ws[layer_idx][i, j] = orig + epsilon
                logits = model.forward(X)
                cost1 = cross_entropy_loss(Y, logits)
                model.ws[layer_idx][i, j] = orig - epsilon
                logits = model.forward(X)
                cost2 = cross_entropy_loss(Y, logits)
                gradient_approximation = (cost1 - cost2) / (2 * epsilon)
                model.ws[layer_idx][i, j] = orig
                # Actual gradient
                logits = model.forward(X)
                model.backward(X, logits, Y)
                difference = gradient_approximation - \
                    model.grads[layer_idx][i, j]
                assert abs(difference) <= epsilon**2,\
                    f"Calculated gradient is incorrect. " \
                    f"Layer IDX = {layer_idx}, i={i}, j={j}.\n" \
                    f"Approximation: {gradient_approximation}, actual gradient: {model.grads[layer_idx][i, j]}\n" \
                    f"If this test fails there could be errors in your cross entropy loss function, " \
                    f"forward function or backward function"


if __name__ == "__main__":
    # Simple test on one-hot encoding
    Y = np.zeros((1, 1), dtype=int)
    Y[0, 0] = 3
    Y = one_hot_encode(Y, 10)
    assert Y[0, 3] == 1 and Y.sum() == 1, \
        f"Expected the vector to be [0,0,0,1,0,0,0,0,0,0], but got {Y}"

    X_train, Y_train, *_ = utils.load_full_mnist()
    mean, std = calculate_mean_and_std(X_train)
    X_train = pre_process_images(X_train, mean, std)
    Y_train = one_hot_encode(Y_train, 10)
    assert X_train.shape[1] == 785,\
        f"Expected X_train to have 785 elements per image. Shape was: {X_train.shape}"

    neurons_per_layer = [64, 10]
    use_improved_sigmoid = True
    use_improved_weight_init = True
    model = SoftmaxModel(
        neurons_per_layer, use_improved_sigmoid, use_improved_weight_init)

    # Gradient approximation check for 100 images
    X_train = X_train[:100]
    Y_train = Y_train[:100]
    for layer_idx, w in enumerate(model.ws):
        model.ws[layer_idx] = np.random.uniform(-1, 1, size=w.shape)

    gradient_approximation_test(model, X_train, Y_train)
