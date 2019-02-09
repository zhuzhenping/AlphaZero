import queue
import numpy as np
import sys


class TrainConfig:

    def __init__(self):
        self.batchSize = 64
        self.maxBatchs = 2**16
        self.maxGames = 2**14
        self.modelSaveBatchs = 10


class TrainData:

    def __init__(self):
        self.inputPlanes = None
        self.inputPolicyMask = None
        self.predictionProbability = None
        self.predictionValue = None


class Trainer:

    def __init__(self, network, MCTS, trainConfig):
        self.network = network
        self.MCTS = MCTS
        self.trainConfig = trainConfig

    def selectActionIndex(self, Pi):
        return np.random.choice(len(Pi), p=Pi)

    def selfPlay(self):
        dataOneGame = []
        self.MCTS.reset()
        while not self.MCTS.game.isTerminated():
            self.MCTS.expandMaxNodes()
            Pi = self.MCTS.Pi()
            if not len(Pi) > 0:
                break
            stepData = TrainData()
            stepData.inputPlanes = self.MCTS.game.getInputPlanes()
            stepData.inputPolicyMask = self.MCTS.game.getInputPolicyMask()
            stepData.predictionProbability = Pi
            actionIndex = self.selectActionIndex(Pi)
            action = self.MCTS.play(actionIndex)
            assert action
            dataOneGame.append(stepData)
        resultValue = self.MCTS.game.getTerminateValue()
        dataOneGame.reverse()
        for data in dataOneGame:
            data.predictionValue = resultValue
            resultValue = -resultValue
        return dataOneGame

    def getBatchData(self, queue):
        inputPlanes = []
        inputPolicyMask = []
        predictionProbability = []
        predictionValue = []
        for i in range(self.trainConfig.batchSize):
            data = queue.get()
            inputPlanes.append(data.inputPlanes)
            inputPolicyMask.append(data.inputPolicyMask)
            predictionProbability.append(data.predictionProbability)
            predictionValue.append(data.predictionValue)
        return inputPlanes, inputPolicyMask, predictionProbability, predictionValue

    def run(self):
        trainDataQueue = queue.Queue()
        batchCount = 0
        gameCount = 0
        while batchCount < self.trainConfig.maxBatchs and gameCount < self.trainConfig.maxGames:
            # generate data by self play
            dataOneGame = self.selfPlay()
            gameCount += 1
            for data in dataOneGame:
                trainDataQueue.put(data)
            # train
            while trainDataQueue.qsize() >= self.trainConfig.batchSize:
                print('.', end='')
                sys.stdout.flush()
                batchCount += 1
                inputPlanes, inputPolicyMask, predictionProbability, predictionValue = self.getBatchData(trainDataQueue)
                self.network.train(inputPlanes, inputPolicyMask, predictionProbability, predictionValue)
                if batchCount % self.trainConfig.modelSaveBatchs == 0:
                    self.network.save()
                    print('save', end='')
                    sys.stdout.flush()
                print('.', end='')
                sys.stdout.flush()

