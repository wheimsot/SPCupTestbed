from PyQt4 import QtGui,QtCore
import main_window
import numpy as np
import scipy.io.wavfile
import pyqtgraph
import sys
import time


class MainWindow(QtGui.QMainWindow, main_window.Ui_MainWindow):
    def __init__(self, parent=None):
        pyqtgraph.setConfigOption('background', 'w')  # before loading widget
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        # Enable/disable required buttons
        self.startButton.setEnabled(False)
        self.fileButton.setEnabled(True)
        # Configure plot
        self.filePlot.plotItem.showGrid(True, True, 0.7)
        # Progress bar initialization and paramters
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        # Wave file paramters
        self.wav_path = ''
        self.wav_data = np.empty(shape=(0, 0), dtype=np.int16)
        self.wav_rate = 0
        # Beat file data
        self.beat_path = ''
        self.beat_times = np.empty(shape=(0, 0), dtype=np.float)
        ### Algorithm parameters
        self.run = False
        # Timing parameters
        self.t0 = 0
        self.end_time = 0
        self.number_chunks = 0
        self.chunk_index = 0
        # Length of data returned
        self.chunk_size = 4096
        # Previous five seconds of audio
        self.chunk_window = np.empty(shape=(0, 0), dtype=np.int16)
        # Most recent audio chunk
        self.cur_chunk = np.empty(shape=(0, 0), dtype=np.int16)

    @QtCore.pyqtSignature("")
    def on_fileButton_clicked(self):
        """
        Update the file plot figure when the choose file button is pressed. Plots the raw audio with annotated
        beat times over top. Only works for the training set provided by the challenge.
        """
        dlg = QtGui.QFileDialog()
        dlg.setFileMode(QtGui.QFileDialog.AnyFile)
        dlg.setFilter("Wave files (*.wav)")
        if dlg.exec_():
            self.wav_path = dlg.selectedFiles()[0]
            self.beat_path = self.wav_path.replace('.wav', '.txt')
            lines = open(self.beat_path).read().splitlines()
            self.beat_times = np.asarray(lines, dtype=np.float)
            self.beatTimes.clearContents()
            for i in range(self.beat_times.size):
                self.beatTimes.setItem(0, i, QtGui.QTableWidgetItem(str(self.beat_times[i])))
            self.wav_rate, self.wav_data = scipy.io.wavfile.read(self.wav_path)
            pen = pyqtgraph.mkPen(color='b')
            symbol_pen = pyqtgraph.mkPen(color='r')
            t = np.arange(0, self.wav_data.size / self.wav_rate, step=1 / self.wav_rate)
            self.filePlot.plot(t, self.wav_data.astype(np.float), pen=pen, clear=True)
            temp = 5000*np.ones_like(self.beat_times)
            self.filePlot.plot(self.beat_times, temp, symbolPen=symbol_pen, symbol='+', clear=False)
            # Enable/disable required buttons
            self.startButton.setEnabled(True)
            self.fileButton.setEnabled(True)
            # Set progress bar parameters
            self.number_chunks = int(self.wav_data.size / self.chunk_size)
            self.progressBar.setMaximum(self.number_chunks)
            self.end_time = self.wav_data.size*(1/self.wav_rate)

    @QtCore.pyqtSignature("")
    def on_startButton_clicked(self):
        print('Starting...')
        self.run = True
        # Initialize the chunk counter
        self.chunk_index = 0
        self.progressBar.setValue(self.chunk_index)
        # Initialize time zero
        self.t0 = time.clock()
        # Grab the first chunk of data
        self.data_callback()
        # Enable/disable required buttons
        self.startButton.setEnabled(False)
        self.fileButton.setEnabled(False)
        # Begin the algorithm by calling it once. It will call itself repeatedly
        self.algorithm()

    def algorithm(self):
        """
        Main algorithm routine. This function will call itself until the entire simulated
        song has been processed in "real time."
        """

        #data = self.queued_data.get()
        """pen = pyqtgraph.mkPen(color='b')
        t = np.arange(0, 4096/22050, step=1/22050)
        self.inputPlot.plot(np.arange(0, stop=self.all_data.size/22050, step=1/22050), self.all_data, pen=pen, clear=True)#np.random.uniform(size=4096), pen=pen, clear=True)
        """
        cur_time = time.clock()
        if cur_time-self.t0 > self.chunk_index*(self.chunk_size/self.wav_rate):
            print('Grabbing new chunk')
            self.data_callback()
            self.progressBar.setValue(self.chunk_index)
            if cur_time > self.end_time + self.t0:
                self.run = False
                # Enable/disable required buttons
                self.startButton.setEnabled(True)
                self.fileButton.setEnabled(True)
                print('Done')
        if self.run:
            # Call itself
            QtCore.QTimer.singleShot(1, self.algorithm)

    def data_callback(self):
        """Function to simulate microphone input"""
        self.cur_chunk = self.wav_data[self.chunk_index*self.chunk_size: self.chunk_index*self.chunk_size+self.chunk_size]
        self.chunk_index += 1

    def closeEvent(self, *args, **kwargs):
        print('Closing...')


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
