from __future__ import annotations

from typing import Tuple

import numpy as np
from scipy import sparse


class LogisticRegression:

    def __init__(self):

        self.w = None
        self.loss_history = None

    def train(self,
              X: np.ndarray,
              y: np.ndarray,
              learning_rate: float = 1e-3,
              reg: float = 1e-5,
              num_iters: int = 100,
              batch_size: int = 200,
              verbose: bool = False) -> LogisticRegression:

        """
        Train this classifier using stochastic gradient descent.

        Inputs:
        - X: N x D array of training data. Each training point is a D-dimensional
             column.
        - y: 1-dimensional array of length N with labels 0-1, for 2 classes.
        - learning_rate: (float) learning rate for optimization.
        - reg: (float) regularization strength.
        - num_iters: (integer) number of steps to take when optimizing
        - batch_size: (integer) number of training examples to use at each step.
        - verbose: (boolean) If true, print progress during optimization.

        Outputs:
        A list containing the value of the loss function at each training iteration.
        """

        # Add a column of ones to X for the bias sake.
        X = LogisticRegression.append_biases(X)
        num_train, dim = X.shape
        if self.w is None:
            # lazily initialize weights
            self.w = np.random.randn(dim) * 0.01

        # Run stochastic gradient descent to optimize W
        self.loss_history = list()
        for it in range(num_iters):
            #########################################################################
            # TODO:                                                                 #
            # Sample batch_size elements from the training data and their           #
            # corresponding labels to use in this round of gradient descent.        #
            # Store the data in X_batch and their corresponding labels in           #
            # y_batch; after sampling X_batch should have shape (batch_size, dim)   #
            # and y_batch should have shape (batch_size,)                           #
            #                                                                       #
            # Hint: Use np.random.choice to generate indices. Sampling with         #
            # replacement is faster than sampling without replacement.              #
            #########################################################################
            batch_indices = np.random.choice(a=X.shape[0], size=batch_size, replace=True)
            X_batch, y_batch = X[batch_indices], y[batch_indices]

            #########################################################################
            #                       END OF YOUR CODE                                #
            #########################################################################

            # evaluate loss and gradient
            loss, grad_w = self.loss(X_batch, y_batch, reg)
            self.loss_history.append(loss)
            # perform parameter update
            #########################################################################
            # TODO:                                                                 #
            # Update the weights using the gradient and the learning rate.          #
            #########################################################################
            self.w -= grad_w * learning_rate

            #########################################################################
            #                       END OF YOUR CODE                                #
            #########################################################################

            if verbose and it % 100 == 0:
                print(f"iteration {it} / {num_iters}: loss {loss}")

        return self

    def predict_proba(self, X: np.ndarray, append_bias: bool = False) -> np.ndarray:

        """
        Use the trained weights of this linear classifier to predict probabilities for
        data points.

        Inputs:
        - X: N x D array of data. Each row is a D-dimensional point.
        - append_bias: bool. Whether to append bias before predicting or not.

        Returns:
        - y_proba: Probabilities of classes for the data in X. y_pred is a 2-dimensional
          array with a shape (N, 2), and each row is a distribution of classes [prob_class_0, prob_class_1].
        """

        if append_bias:
            X = LogisticRegression.append_biases(X)
        ###########################################################################
        # TODO:                                                                   #
        # Implement this method. Store the probabilities of classes in y_proba.   #
        # Hint: It might be helpful to use np.vstack and np.sum                   #
        ###########################################################################
        y_one = self._predict_probability_for_class_one(X)
        y_zero = 1.0 - y_one
        y_proba = np.hstack((y_zero[:, np.newaxis], y_one[:, np.newaxis]))

        ###########################################################################
        #                           END OF YOUR CODE                              #
        ###########################################################################
        return y_proba

    def predict(self, X: np.ndarray) -> np.ndarray:

        """
        Use the ```predict_proba``` method to predict labels for data points.

        Inputs:
        - X: N x D array of training data. Each column is a D-dimensional point.

        Returns:
        - y_pred: Predicted labels for the data in X. y_pred is a 1-dimensional
          array of length N, and each element is an integer giving the predicted
          class.
        """

        ###########################################################################
        # TODO:                                                                   #
        # Implement this method. Store the predicted labels in y_pred.            #
        ###########################################################################
        y_proba = self.predict_proba(X, append_bias=True)
        y_pred = y_proba.argmax(axis=1)

        ###########################################################################
        #                           END OF YOUR CODE                              #
        ###########################################################################
        return y_pred

    def _predict_probability_for_class_one(self, X: np.ndarray) -> np.ndarray:

        """
        Makes prediction for class one in case of binary classification
        :param X: feature matrix
        :return: numpy array with predictions for class one
        """

        prediction_probability_for_class_one = 1.0 / (1.0 + np.exp(-X.dot(self.w)))
        return prediction_probability_for_class_one

    def loss(self,
             X_batch: np.ndarray,
             y_batch: np.ndarray,
             reg: float) -> Tuple[float, np.ndarray]:

        """
        Logistic Regression loss function
        Inputs:
        - X: N x D array of data. Data are D-dimensional rows
        - y: 1-dimensional array of length N with labels 0-1, for 2 classes
        Returns:
        a tuple of:
        - loss as single float
        - gradient with respect to weights w; an array of same shape as w
        """

        # Compute loss and gradient. Your code should not contain python loops.
        #
        # Right now the loss is a sum over all training examples, but we want it
        # to be an average instead so we divide by num_train.
        # Note that the same thing must be done with gradient.

        prediction_one = self._predict_probability_for_class_one(X_batch)
        loss = (-y_batch.dot(np.log(prediction_one)) - (1 - y_batch).dot(np.log(1 - prediction_one))) / X_batch.shape[0]
        dw = (prediction_one - y_batch) * X_batch / X_batch.shape[0]

        # Add regularization to the loss and gradient.
        # Note that you have to exclude bias term in regularization.
        loss += reg * self.w[:-1].dot(self.w[:-1])
        dw[:-1] += reg * self.w[:-1]

        return loss, dw

    @staticmethod
    def append_biases(X):
        return sparse.hstack((X, np.ones(X.shape[0])[:, np.newaxis])).tocsr()
