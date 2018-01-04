import time
import math
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.recurrent import LSTM
import numpy as np
import pandas as pd
import sklearn.preprocessing as prep
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt2
import random
import sys

# this script is called when only futures price information is available.


# normalize the input
def standard_scaler(file_name, stock_name, normalize=True):
    df = pd.read_excel(file_name, sheetname=stock_name)
    if shape[0]==1 and normalize:
        # normalize the price by using min-max normalization
        min_max_scaler = prep.MinMaxScaler()
        df['price'] = min_max_scaler.fit_transform(df['price'].values.reshape(-1,1))
    # this will not be used here
    if shape[0]==2 and normalize:
        min_max_scaler = prep.MinMaxScaler()
        df['price'] = min_max_scaler.fit_transform(df['price'].values.reshape(-1,1))
        df['opinion'] = min_max_scaler.fit_transform(df['opinion'].values.reshape(-1,1))
    return df

# form input according to the window size
def preprocess_data(stock, seq_len):
    amount_of_features = len(stock.columns)
    data = stock.as_matrix()

#    plt2.plot(data.T[0][0:30], color='red', label='price')
#    plt2.legend(loc='upper left')
#    plt2.show()
    
    sequence_length = seq_len + 1
    result = []
    # form
    for index in range(len(data) - sequence_length):
        result.append(data[index : index + sequence_length])
        
    result = np.array(result)
    # 10% hold out
    row = round(0.9 * result.shape[0])
    train = result[: int(row), :]
    
    X_train = train[:, : -1]
    y_train = train[:, -1][: ,-1]
    # last 10% data is used for test purpose
    X_test = result[int(row) :, : -1]
    y_test = result[int(row) :, -1][ : ,-1]

    # use all data for test purpose
    X_test_all = result[:,: -1]
    y_test_all = result[:, -1][ : ,-1]

    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], amount_of_features))
    X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], amount_of_features))
    X_test_all = np.reshape(X_test_all, (X_test_all.shape[0], X_test_all.shape[1], amount_of_features))

    return [X_train, y_train, X_test, y_test, X_test_all, y_test_all]


def build_model(layers, neurons, d):
    model = Sequential()

    # By setting return_sequences to True we are able to stack another LSTM layer
    model.add(LSTM(
        neurons[0],
        input_shape =(layers[1],layers[0]),
        return_sequences=True))
    model.add(Dropout(d))
    
    model.add(LSTM(
        neurons[1],
        input_shape=(layers[1],layers[0]),
        return_sequences=False))
    model.add(Dropout(d))

    model.add(Dense(neurons[2], activation='relu', kernel_initializer='uniform'))
    model.add(Dense(neurons[3], activation='linear', kernel_initializer='uniform'))

    start = time.time()
    model.compile(loss="mse", optimizer="rmsprop", metrics=['accuracy'])
    print("Compilation Time : ", time.time() - start)
    model.summary()
    return model

price_input = sys.argv[1]
stock_name = sys.argv[2]
print("testing for: ", stock_name)

for window in range(18,50):
    # shape[#number of feature, the window size, the output size]
    shape = [1, window, 1]
    # the number of neurons in each layer
    neurons = [128,128,32,1]
    # dropout rate
    d=0.2
    df = standard_scaler(price_input, stock_name, normalize=True)

    X_train, y_train, X_test, y_test, X_test_all, y_test_all = preprocess_data(df, window)

    model = build_model(shape, neurons, d)

    model.fit(
        X_train,
        y_train,
        batch_size=32,
        epochs=100,
        validation_split=0.05,
        verbose=0)

    pred = model.predict(X_test)

    #plt2.plot(pred, color='red', label='Prediction')
    #plt2.plot(y_test, color='blue', label='Ground Truth')
    #plt2.legend(loc='upper left')
    #plt2.show()

    f_star=[]
    f = []
    v_star=[]
    v=[]
    # check whether the volatility is positive or negative
    for i in range(pred.size-1):
        f_star.append((pred[i+1]-pred[i]>0))
        f.append((y_test[i+1]-y_test[i])>0)
    counter = 0
    # count the number of correct prediction
    for i in range(len(f)):
        if f_star[i][0] == f[i]:
            counter += 1
    acc = counter * 1.0 / (len(f))
    print "window: "+str(window)+" accuracy: " + str(acc)

    # test for all data
    pred2 = model.predict(X_test_all)

    #plt2.plot(pred2, color='red', label='Prediction')
    #plt2.plot(y_test_all, color='blue', label='Ground Truth')
    #plt2.legend(loc='upper left')
    #plt2.show()

    f_star2=[]
    f2 = []
    #v_star2=[]
    #v2=[]

    # check whether the volatility is positive or negative
    for i in range(pred2.size-1):
        f_star2.append((pred2[i+1]-pred2[i]>0))
        f2.append((y_test_all[i+1]-y_test_all[i])>0)
    counter = 0

    for i in range(len(f2)):
        if f_star2[i][0] == f2[i]:
            counter += 1
    acc = counter * 1.0 / (len(f2))
    print "Test for all data: window: "+str(window)+" accuracy: " + str(acc)
