# cnn model
import numpy as np
# set the seeds for consistency
seed = 1
np.random.seed(seed)# set the numpy seed before importing keras
import random
random.seed(seed) #set the build-in seed
import tensorflow as tf
tf.random.set_seed(seed) # set the seed for tf
import pandas as pd
from numpy import dstack
from keras.models import Sequential
from keras.layers import Dense,BatchNormalization
from keras.layers import Flatten
from keras.layers.convolutional import Conv1D
from keras.utils import np_utils
from keras.utils.vis_utils import plot_model
from timeit import default_timer as timer
from matplotlib import pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.utils import class_weight
from plot_confusion_matrix import cm_analysis


# load the labels file as a numpy array
def load_file(filepath):
    labels = np.loadtxt(filepath, str)
    return labels

# load a list of files and return as a 3d numpy array
def load_group(filenames, prefix=''):
    loaded = list()
    for name in filenames:
        data = np.loadtxt(prefix + name, ndmin = 2)
        loaded.append(data)
    # stack group so that features are the 3rd dimension
    loaded = dstack(loaded)
    return loaded

#load a dataset group, such as train or test
def load_dataset_group(group, prefix = ''):
    #load all 3 files as a single array
    filenames = list()
    # acceleration
    filenames += [group+'_acc_x.txt', group+'_acc_y.txt', group+'_acc_z.txt']
    # load input data
    X = load_group(filenames, prefix)
    # load class output
    y = load_file(prefix + group + 'y.txt') #testy/ trainy
    return X, y

#load the dataset, returns train and test X and y elements
def load_dataset():
    # load all train
    trainX, trainy = load_dataset_group('train', 'DP13_old3/')
    print('trainX shape: ', trainX.shape, 'trainy shape :', trainy.shape)
    # load all test
    testX, testy = load_dataset_group('test', 'DP13_old3/')
    print('testX shape: ', testX.shape, 'testy shape', testy.shape)
    print('train class',pd.DataFrame(trainy).groupby(0).size())
    return trainX, trainy, testX, testy

trainX, trainy, testX, testy = load_dataset()

# encode class as integers
le = LabelEncoder()
le.fit(trainy)
le.fit(testy)
int_trainy = le.transform(trainy)
int_testy = le.transform(testy)
# convert integers to one hot encode
dum_trainy = np_utils.to_categorical(int_trainy)
dum_testy = np_utils.to_categorical(int_testy)
print('trainX shape: ', trainX.shape, 'trainy one hot shape :', dum_trainy.shape,
      '\ntestX shape: ', testX.shape, 'testy one hot shape: ', dum_testy.shape)

# build a model
def build_model(X, y):

    # define model
    model = Sequential()
    model.add(Conv1D(filters= 35, kernel_size = 3, activation = 'relu', input_shape=(X.shape[1], X.shape[2])))
    model.add(Conv1D(filters = 35, kernel_size = 3, activation = 'relu'))
    model.add(Flatten())
    model.add(Dense(64,activation='relu'))
    model.add(Dense(y.shape[1], activation='softmax'))
    model.compile(loss='categorical_crossentropy',optimizer='Adadelta',
                  metrics=['accuracy'])

    return model

# run the experiment
trainy_encode = np.argmax(dum_trainy, axis =1) # the column index of max value for each line
weights = class_weight.compute_class_weight('balanced',
                                            np.unique(trainy_encode),trainy_encode)
dict_weights = dict(enumerate(weights))
print('dict_weights:\n',dict_weights)
model = build_model(trainX, dum_trainy)

# fit the model
verbose, epochs, batch_size = 1, 30, 128
start = timer()
history = model.fit(trainX, dum_trainy, epochs=epochs, batch_size=batch_size,
                    class_weight=dict_weights, verbose=verbose) #
end = timer()
print('> training time:',end-start)
# evaluate the model

test_loss, test_accuracy = model.evaluate(testX, dum_testy, batch_size=batch_size, verbose=verbose)
test_accuracy = test_accuracy * 100
print(f'> loss={test_loss}, accuracy={test_accuracy}')

# predict the test set
start = timer()
pred = model.predict(testX) # get the probabilities of each class
end = timer()
print(f'> testing time: {end-start}')
# get the column index of max in each row, then transform to the label names
int_predy = np.argmax(pred, axis = 1)
pred_y = le.inverse_transform(int_predy)
print(model.summary())

# classification report
from sklearn.metrics import classification_report
target_names = ['Lying','Sitting','Standing','Transition','Walking','Walking Down','Walking Up']
print(classification_report(int_testy, int_predy, target_names = target_names,digits =4))

# save confusion matrix
cm_analysis(testy, pred_y, filename='DP13_pics/DP13_CNN_CM.png',
            labels=['Lying','Sitting','Standing','Transition',
                    'Walking','WalkingDown','WalkingUp'])
