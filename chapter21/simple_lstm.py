from chapter21.load_data import load_dataset
from pandas import DataFrame, concat
from keras.models import Sequential
from keras.layers import LSTM, Dense
from keras.optimizers import SGD
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from matplotlib import pyplot as plt

batch_size = 5
epochs = 200
# 通过过去几次的数据进行预测
n_input = 20

def convert_dataset(data, n_input=1, dropnan=True):
    n_vars = 1 if type(data) is list else data.shape[1]
    df = DataFrame(data)
    cols, names = [], []
    # 输入序列 (t-n, ... t-1)
    for i in range(n_input, 0, -1):
        cols.append(df.shift(i))
        names += [('var%d(t-%d)' % (j + 1, i)) for j in range(n_vars)]
    # 输出结果 (t)
    cols.append(df[df.columns[0]])
    names += ['result']
    # 合并输入输出序列
    result = concat(cols, axis=1)
    result.columns = names
    # 删除包含缺失值的行
    if dropnan:
        result.dropna(inplace=True)
    return result


# class_indexs 编码的字段序列号，或者序列号List，列号从0开始
def class_encode(data, class_indexs):
    encoder = LabelEncoder()
    class_indexs = class_indexs if type(class_indexs) is list else [class_indexs]

    values = DataFrame(data).values

    for index in class_indexs:
        values[:, index] = encoder.fit_transform(values[:, index])

    return DataFrame(values) if type(data) is DataFrame else values

def build_model(lstm_input_shape):
    model = Sequential()
    model.add(LSTM(units=128, input_shape=lstm_input_shape, return_sequences=True))
    model.add(LSTM(units=256, return_sequences=True, dropout=0.2, recurrent_dropout=0.2))
    model.add(LSTM(units=128, return_sequences=True, dropout=0.2, recurrent_dropout=0.2))
    model.add(LSTM(units=72, dropout=0.2, recurrent_dropout=0.2))
    model.add(Dense(1))
    optimizer = SGD(lr=0.9, momentum=0.9, decay=0.01)
    model.compile(loss='mae', optimizer=optimizer)
    model.summary()
    return model

if __name__ == '__main__':
    # 导入数据
    data = load_dataset()
    # 对风向列进行编码
    data = class_encode(data, 4)
    # 生成数据集，使用前5次的数据，来预测新数据
    dataset = convert_dataset(data, n_input=n_input)
    values = dataset.values.astype('float32')

    # 分类训练与评估数据集
    n_train_hours = len(values) - 50
    train = values[:n_train_hours, :]
    validation = values[n_train_hours:, :]
    x_train, y_train = train[:, :-1], train[:, -1]
    x_validation, y_validation = validation[:, :-1], validation[:, -1]

    # 数据归一元(0-1之间)
    scaler = MinMaxScaler()
    x_train = scaler.fit_transform(x_train)
    x_validation = scaler.fit_transform(x_validation)

    # 将数据整理成【样本，时间步长，特征】结构
    x_train = x_train.reshape(x_train.shape[0], 1, x_train.shape[1])
    x_validation = x_validation.reshape(x_validation.shape[0], 1, x_validation.shape[1])
    # 查看数据维度
    print(x_train.shape, y_train.shape, x_validation.shape, y_validation.shape)

    # 训练模型
    lstm_input_shape = (x_train.shape[1], x_train.shape[2])
    model = build_model(lstm_input_shape)
    model.fit(x_train, y_train, batch_size=batch_size, validation_data=(x_validation, y_validation), epochs=epochs, verbose=2)

    # 使用模型预测评估数据集
    prediction = model.predict(x_validation)

    # 图表显示
    plt.plot(y_validation, color='blue', label='Actual')
    plt.plot(prediction, color='green', label='Prediction')
    plt.legend(loc='upper right')
    plt.show()