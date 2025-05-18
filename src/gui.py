import os
import time
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                           QLabel, QPushButton, QTextEdit, QMessageBox, 
                           QFileDialog, QHBoxLayout, QComboBox, QGroupBox,
                           QProgressDialog)
from PyQt5.QtCore import Qt
from core import sign_file, verify_file, CryptoError, gost34112012256
from gost.gost341012 import GOST3410Curve, CURVE_PARAMS, prv_unmarshal, public_key

class GOSTSignatureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ГОСТ 34.10-2018 Электронная подпись")
        self.curve = None
        self.private_key = None
        self.public_key = None
        self.current_curve = "GostR3410_2018_256_ParamSetA"
        self.setup_ui()
        
    def setup_ui(self):
        self.tabs = QTabWidget()
        
        # Вкладка ключей
        self.setup_keys_tab()
        # Вкладка подписи
        self.setup_sign_tab()
        # Вкладка проверки
        self.setup_verify_tab()
        # Вкладка инструкции
        self.setup_help_tab()
        
        self.setCentralWidget(self.tabs)
        self.statusBar().showMessage("Готово")
    
    def setup_keys_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Выбор параметров кривой
        curve_group = QGroupBox("Параметры кривой")
        curve_layout = QVBoxLayout()
        
        self.curve_combo = QComboBox()
        self.curve_combo.addItems(CURVE_PARAMS.keys())
        self.curve_combo.setCurrentText(self.current_curve)
        curve_layout.addWidget(QLabel("Выберите параметры кривой:"))
        curve_layout.addWidget(self.curve_combo)
        
        curve_group.setLayout(curve_layout)
        layout.addWidget(curve_group)
        
        # Генерация ключей
        key_group = QGroupBox("Управление ключами")
        key_layout = QVBoxLayout()
        
        self.generate_btn = QPushButton("Сгенерировать ключевую пару")
        self.generate_btn.clicked.connect(self.generate_keys)
        key_layout.addWidget(self.generate_btn)
        
        self.key_status = QLabel("Ключи не сгенерированы")
        key_layout.addWidget(self.key_status)
        
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # О программе
        about_btn = QPushButton("О программе")
        about_btn.clicked.connect(self.show_about)
        layout.addWidget(about_btn)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Ключи")
    
    def setup_sign_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Выбор файла
        file_group = QGroupBox("Файл для подписи")
        file_layout = QVBoxLayout()
        
        self.file_path_label = QLabel("Файл не выбран")
        file_layout.addWidget(self.file_path_label)
        
        self.select_file_btn = QPushButton("Выбрать файл")
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_file_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Подпись
        self.sign_btn = QPushButton("Подписать файл")
        self.sign_btn.clicked.connect(self.sign_file)
        self.sign_btn.setEnabled(False)
        layout.addWidget(self.sign_btn)
        
        # Визуализация
        self.visualization = QTextEdit()
        self.visualization.setReadOnly(True)
        layout.addWidget(self.visualization)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Подпись")
    
    def setup_verify_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Выбор файла
        verify_file_group = QGroupBox("Файл для проверки")
        verify_file_layout = QVBoxLayout()
        
        self.verify_file_path_label = QLabel("Файл не выбран")
        verify_file_layout.addWidget(self.verify_file_path_label)
        
        self.select_verify_file_btn = QPushButton("Выбрать файл")
        self.select_verify_file_btn.clicked.connect(self.select_verify_file)
        verify_file_layout.addWidget(self.select_verify_file_btn)
        
        verify_file_group.setLayout(verify_file_layout)
        layout.addWidget(verify_file_group)
        
        # Выбор подписи
        verify_sig_group = QGroupBox("Файл подписи")
        verify_sig_layout = QVBoxLayout()
        
        self.verify_sig_path_label = QLabel("Подпись не выбрана")
        verify_sig_layout.addWidget(self.verify_sig_path_label)
        
        self.select_verify_sig_btn = QPushButton("Выбрать подпись")
        self.select_verify_sig_btn.clicked.connect(self.select_verify_sig)
        verify_sig_layout.addWidget(self.select_verify_sig_btn)
        
        verify_sig_group.setLayout(verify_sig_layout)
        layout.addWidget(verify_sig_group)
        
        # Проверка
        self.verify_btn = QPushButton("Проверить подпись")
        self.verify_btn.clicked.connect(self.verify_file)
        self.verify_btn.setEnabled(False)
        layout.addWidget(self.verify_btn)
        
        # Результат
        self.verify_result = QLabel("")
        layout.addWidget(self.verify_result)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Проверка")
    
    def setup_help_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>Как пользоваться программой</h2>
        
        <h3>1. Создание ключей</h3>
        <p>На вкладке "Ключи":</p>
        <ul>
            <li>Выберите параметры кривой (можно оставить по умолчанию)</li>
            <li>Нажмите "Сгенерировать ключевую пару"</li>
            <li>Дождитесь сообщения об успешной генерации</li>
        </ul>
        <p><b>Важно:</b> Ключи хранятся только в памяти программы. После закрытия программы их нужно будет создать заново.</p>
        
        <h3>2. Подпись файла</h3>
        <p>На вкладке "Подпись":</p>
        <ul>
            <li>Убедитесь, что ключи уже сгенерированы</li>
            <li>Нажмите "Выбрать файл" и укажите файл для подписи</li>
            <li>Нажмите "Подписать файл"</li>
            <li>Дождитесь завершения процесса</li>
        </ul>
        <p><b>Результат:</b> Рядом с исходным файлом появится файл с расширением .sign</p>
        
        <h3>3. Проверка подписи</h3>
        <p>На вкладке "Проверка":</p>
        <ul>
            <li>Нажмите "Выбрать файл" и укажите подписанный файл</li>
            <li>Нажмите "Выбрать подпись" и укажите файл .sign</li>
            <li>Нажмите "Проверить подпись"</li>
        </ul>
        <p><b>Результат проверки:</b></p>
        <ul>
            <li>Зелёным цветом - подпись верна</li>
            <li>Красным цветом - подпись неверна</li>
        </ul>
        
        <h3>Советы</h3>
        <ul>
            <li>Всегда проверяйте подпись после её создания</li>
            <li>Храните файлы подписи (.sign) вместе с подписанными файлами</li>
            <li>Если файл был изменён после подписи, проверка покажет, что подпись неверна</li>
        </ul>
        
        <h3>О программе</h3>
        <p>Программа использует:</p>
        <ul>
            <li>ГОСТ 34.10-2018 для создания электронной подписи</li>
            <li>ГОСТ 34.11-2012 (Streebog) для вычисления хэша</li>
        </ul>
        """)
        
        layout.addWidget(help_text)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Инструкция")
    
    def generate_keys(self):
        try:
            self.current_curve = self.curve_combo.currentText()
            curve_params = CURVE_PARAMS[self.current_curve]
            self.curve = GOST3410Curve(*curve_params)
            
            # Генерация случайного приватного ключа
            key_size = 32 if "256" in self.current_curve else 64
            prv_raw = os.urandom(key_size)
            self.private_key = prv_unmarshal(prv_raw)
            
            # Вычисление публичного ключа
            self.public_key = public_key(self.curve, self.private_key)
            
            self.key_status.setText(
                f"Ключи сгенерированы\nКривая: {self.current_curve}\n"
                f"Размер: {key_size*8} бит"
            )
            self.sign_btn.setEnabled(True)
            self.update_visualization("Ключевая пара успешно сгенерирована")
            self.statusBar().showMessage("Ключи сгенерированы")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка генерации ключей: {str(e)}")
            self.update_visualization(f"Ошибка генерации ключей: {str(e)}")
    
    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл для подписи")
        if path:
            self.file_path_label.setText(path)
            self.update_visualization(f"Выбран файл: {path}")
    
    def sign_file(self):
        if not self.private_key or not self.curve:
            QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте ключи")
            return
            
        path = self.file_path_label.text()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Ошибка", "Файл не выбран или не существует")
            return
            
        try:
            # Создаем прогресс-бар до начала операций
            progress = QProgressDialog("Подготовка к подписанию...", None, 0, 100, self)
            progress.setWindowTitle("Прогресс")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.setCancelButton(None)  # Убираем кнопку отмены
            progress.setAutoClose(False)    # Запрещаем автоматическое закрытие
            progress.setAutoReset(False)    # Запрещаем автоматический сброс
            
            # Имитация подготовки (чтобы пользователь видел, что процесс начался)
            for i in range(10):
                progress.setValue(i)
                progress.setLabelText(f"Подготовка к подписанию... {i*10}%")
                QApplication.processEvents()  # Обработка событий для отображения прогресса
                time.sleep(0.1)  # Небольшая задержка для визуализации
            
            self.update_visualization("Начало процесса подписи...")
            progress.setValue(10)
            progress.setLabelText("Вычисление хэша (Streebog-256)...")
            
            # Вычисляем хэш
            with open(path, 'rb') as f:
                data = f.read()
                # Показываем прогресс чтения файла
                file_size = os.path.getsize(path)
                chunk_size = 1024 * 1024  # 1MB
                bytes_read = 0
                while bytes_read < file_size:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
                    progress_value = 10 + int((bytes_read / file_size) * 30)
                    progress.setValue(progress_value)
                    progress.setLabelText(f"Чтение файла... {int((bytes_read / file_size) * 100)}%")
                    QApplication.processEvents()
            
            digest = gost34112012256(data)
            progress.setValue(40)
            
            # Подписываем
            self.update_visualization("Генерация подписи...")
            progress.setLabelText("Генерация подписи...")
            
            # Имитация процесса подписи
            for i in range(40, 90, 5):
                progress.setValue(i)
                progress.setLabelText(f"Генерация подписи... {i-40}%")
                QApplication.processEvents()
                time.sleep(0.05)
            
            if sign_file(path, self.curve, self.private_key):
                progress.setValue(90)
                progress.setLabelText("Завершение операции...")
                self.update_visualization("Файл успешно подписан!")
                
                # Плавное завершение
                for i in range(90, 101, 2):
                    progress.setValue(i)
                    QApplication.processEvents()
                    time.sleep(0.02)
                
                QMessageBox.information(self, "Успех", "Файл успешно подписан")
                self.statusBar().showMessage("Подпись создана")
        except CryptoError as e:
            self.update_visualization(f"Ошибка подписи: {str(e)}")
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            if 'progress' in locals():
                progress.close()
    
    def select_verify_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл для проверки")
        if path:
            self.verify_file_path_label.setText(path)
            self.check_verify_ready()
    
    def select_verify_sig(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл подписи", "", "Signature Files (*.sign)")
        if path:
            self.verify_sig_path_label.setText(path)
            self.check_verify_ready()
    
    def check_verify_ready(self):
        if (self.verify_file_path_label.text() != "Файл не выбран" and 
            self.verify_sig_path_label.text() != "Подпись не выбрана"):
            self.verify_btn.setEnabled(True)
    
    def verify_file(self):
        file_path = self.verify_file_path_label.text()
        sig_path = self.verify_sig_path_label.text()
        
        try:
            # Создаем прогресс-бар до начала операций
            progress = QProgressDialog("Подготовка к проверке...", None, 0, 100, self)
            progress.setWindowTitle("Прогресс проверки")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.setCancelButton(None)  # Убираем кнопку отмены
            progress.setAutoClose(False)    # Запрещаем автоматическое закрытие
            progress.setAutoReset(False)    # Запрещаем автоматический сброс
            
            # Имитация подготовки
            for i in range(10):
                progress.setValue(i)
                progress.setLabelText(f"Подготовка к проверке... {i*10}%")
                QApplication.processEvents()
                time.sleep(0.1)
            
            self.update_visualization("Начало проверки подписи...")
            progress.setValue(10)
            progress.setLabelText("Чтение файла подписи...")
            
            # Чтение файла подписи
            with open(sig_path, 'rb') as f:
                sig_data = f.read()
                progress.setValue(20)
            
            # Чтение проверяемого файла
            progress.setLabelText("Чтение проверяемого файла...")
            with open(file_path, 'rb') as f:
                # Показываем прогресс чтения файла
                file_size = os.path.getsize(file_path)
                chunk_size = 1024 * 1024  # 1MB
                bytes_read = 0
                while bytes_read < file_size:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
                    progress_value = 20 + int((bytes_read / file_size) * 30)
                    progress.setValue(progress_value)
                    progress.setLabelText(f"Чтение файла... {int((bytes_read / file_size) * 100)}%")
                    QApplication.processEvents()
            
            progress.setValue(50)
            progress.setLabelText("Вычисление хэша...")
            
            # Имитация процесса проверки
            for i in range(50, 90, 5):
                progress.setValue(i)
                progress.setLabelText(f"Проверка подписи... {i-50}%")
                QApplication.processEvents()
                time.sleep(0.05)
            
            result = verify_file(file_path, sign_path=sig_path)
            
            progress.setValue(90)
            progress.setLabelText("Завершение проверки...")
            
            # Плавное завершение
            for i in range(90, 101, 2):
                progress.setValue(i)
                QApplication.processEvents()
                time.sleep(0.02)
            
            if result:
                self.verify_result.setText("Подпись ВЕРНА")
                self.verify_result.setStyleSheet("color: green; font-weight: bold;")
                self.update_visualization("Проверка завершена: подпись верна")
            else:
                self.verify_result.setText("Подпись НЕВЕРНА")
                self.verify_result.setStyleSheet("color: red; font-weight: bold;")
                self.update_visualization("Проверка завершена: подпись недействительна")
                
            self.statusBar().showMessage("Проверка завершена")
        except CryptoError as e:
            self.verify_result.setText("Ошибка проверки")
            self.update_visualization(f"Ошибка проверки: {str(e)}")
            QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            if 'progress' in locals():
                progress.close()
    
    def show_about(self):
        about_text = """<b>ГОСТ 34.10-2018 Электронная подпись</b>
        <p>Версия: 0.1
        <p>Разработчик: [8BIT]
        <p>Год: 2025
        <p>Реализация стандартов:
        <ul>
          <li>ГОСТ 34.10-2018 (ЭЦП)
          <li>ГОСТ 34.11-2012 (Streebog)
        </ul>
        <p>Лицензия: GNU GPL v3"""
        QMessageBox.about(self, "О программе", about_text)
    
    def update_visualization(self, message):
        self.visualization.append(message)
        self.visualization.ensureCursorVisible()

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = GOSTSignatureApp()
    window.show()
    sys.exit(app.exec_())