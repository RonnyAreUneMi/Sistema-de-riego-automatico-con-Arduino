# main_app.py - Aplicación principal con PyQt5
import sys
import json
import serial
import threading
import time
import webbrowser
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns

class DataCollectorThread(QThread):
    """Hilo para recolección de datos del Arduino"""
    data_updated = pyqtSignal(dict)
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, puerto='COM7', baudrate=115200):
        super().__init__()
        self.puerto = puerto
        self.baudrate = baudrate
        self.running = False
        self.serial_conn = None
        self.datos = {
            'humedad': [],
            'temperatura': [],
            'eventos': [],
            'estadisticas': {
                'total_riegos': 0,
                'humedad_promedio': 0,
                'temperatura_promedio': 0,
                'ultimo_riego': None
            }
        }
        
    def run(self):
        """Bucle principal de recolección"""
        try:
            self.serial_conn = serial.Serial(self.puerto, self.baudrate, timeout=1)
            self.running = True
            self.status_updated.emit(f"✅ Conectado a {self.puerto}")
            
            while self.running:
                if self.serial_conn.in_waiting > 0:
                    linea = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if linea:
                        self.procesar_linea(linea)
                        
                self.msleep(100)  # Pausa de 100ms
                
        except Exception as e:
            self.error_occurred.emit(f"Error de conexión: {str(e)}")
            
    def procesar_linea(self, linea):
        """Procesa datos del Arduino"""
        timestamp = datetime.now()
        
        try:
            # Extraer humedad
            if "Humedad:" in linea:
                humedad = int(linea.split("Humedad:")[1].split('%')[0].strip())
                self.datos['humedad'].append({
                    'timestamp': timestamp,
                    'valor': humedad
                })
                
                # Mantener solo últimos 100 registros
                if len(self.datos['humedad']) > 100:
                    self.datos['humedad'] = self.datos['humedad'][-100:]
                    
            # Extraer temperatura
            if "Temp:" in linea:
                temp_str = linea.split("Temp:")[1].split('C')[0].strip()
                if temp_str != "Error":
                    temperatura = float(temp_str)
                    self.datos['temperatura'].append({
                        'timestamp': timestamp,
                        'valor': temperatura
                    })
                    
                    if len(self.datos['temperatura']) > 100:
                        self.datos['temperatura'] = self.datos['temperatura'][-100:]
            
            # Detectar eventos
            if "Riego iniciado" in linea:
                self.datos['eventos'].append({
                    'timestamp': timestamp,
                    'tipo': 'riego_iniciado',
                    'descripcion': 'Bomba activada'
                })
                self.datos['estadisticas']['total_riegos'] += 1
                self.datos['estadisticas']['ultimo_riego'] = timestamp.strftime("%H:%M:%S")
                
            elif "Bomba OFF" in linea:
                self.datos['eventos'].append({
                    'timestamp': timestamp,
                    'tipo': 'riego_terminado',
                    'descripcion': 'Bomba desactivada'
                })
            
            # Actualizar estadísticas
            self.actualizar_estadisticas()
            
            # Emitir señal con datos actualizados
            self.data_updated.emit(self.datos.copy())
            
        except Exception as e:
            self.error_occurred.emit(f"Error procesando datos: {str(e)}")
    
    def actualizar_estadisticas(self):
        """Actualiza estadísticas generales"""
        if self.datos['humedad']:
            valores = [d['valor'] for d in self.datos['humedad']]
            self.datos['estadisticas']['humedad_promedio'] = sum(valores) / len(valores)
        
        if self.datos['temperatura']:
            valores = [d['valor'] for d in self.datos['temperatura']]
            self.datos['estadisticas']['temperatura_promedio'] = sum(valores) / len(valores)
    
    def stop(self):
        """Detiene la recolección"""
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()

class MatplotlibWidget(QWidget):
    """Widget personalizado para gráficos matplotlib"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Configurar estilo
        try:
            plt.style.use('seaborn-v0_8-whitegrid')
        except:
            plt.style.use('default')
        
    def actualizar_graficos(self, datos):
        """Actualiza todos los gráficos con nuevos datos"""
        self.figure.clear()
        
        # Crear subplots
        gs = self.figure.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # 1. Gráfico de humedad
        ax1 = self.figure.add_subplot(gs[0, :])
        if datos['humedad']:
            timestamps = [d['timestamp'] for d in datos['humedad']]
            valores = [d['valor'] for d in datos['humedad']]
            
            ax1.plot(timestamps, valores, marker='o', linewidth=2, color='#2E8B57', markersize=4)
            ax1.axhline(y=30, color='red', linestyle='--', alpha=0.7, label='Umbral Riego (30%)')
            ax1.axhline(y=45, color='green', linestyle='--', alpha=0.7, label='Umbral Satisfecho (45%)')
            ax1.set_title('Humedad del Suelo en Tiempo Real', fontweight='bold', fontsize=14)
            ax1.set_ylabel('Humedad (%)')
            ax1.set_ylim(0, 100)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Formato de fechas en eje X
            if len(timestamps) > 10:
                ax1.tick_params(axis='x', rotation=45)
        
        # 2. Gráfico de temperatura
        ax2 = self.figure.add_subplot(gs[1, 0])
        if datos['temperatura']:
            timestamps = [d['timestamp'] for d in datos['temperatura']]
            valores = [d['valor'] for d in datos['temperatura']]
            
            ax2.plot(timestamps, valores, marker='s', linewidth=2, color='#FF6347', markersize=4)
            ax2.set_title('🌡️ Temperatura', fontweight='bold')
            ax2.set_ylabel('Temperatura (°C)')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
        
        # 3. Distribución de humedad
        ax3 = self.figure.add_subplot(gs[1, 1])
        if datos['humedad']:
            valores = [d['valor'] for d in datos['humedad']]
            ax3.hist(valores, bins=15, alpha=0.7, color='#2E8B57', edgecolor='black')
            ax3.axvline(x=30, color='red', linestyle='--', alpha=0.7)
            ax3.axvline(x=45, color='green', linestyle='--', alpha=0.7)
            ax3.set_title('📊 Distribución Humedad', fontweight='bold')
            ax3.set_xlabel('Humedad (%)')
            ax3.set_ylabel('Frecuencia')
        
        self.canvas.draw()
    
    def exportar_imagen(self, filename):
        """Exporta los gráficos como imagen"""
        try:
            self.figure.savefig(filename, dpi=300, bbox_inches='tight', 
                              facecolor='white', edgecolor='none')
            return True
        except Exception as e:
            print(f"Error exportando imagen: {str(e)}")
            return False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.collector_thread = None
        self.datos_actuales = {}
        
        self.init_ui()
        self.setup_statusbar()
        
    def init_ui(self):
        """Inicializa la interface de usuario"""
        self.setWindowTitle('Sistema de Riego Automático - Monitor Profesional')
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # === PANEL IZQUIERDO - CONTROLES ===
        control_panel = self.crear_panel_control()
        main_layout.addWidget(control_panel, 1)
        
        # === PANEL DERECHO - GRÁFICOS ===
        self.graficos_widget = MatplotlibWidget()
        main_layout.addWidget(self.graficos_widget, 3)
        
        # Crear menú
        self.crear_menu()
        
    def crear_panel_control(self):
        """Crea el panel de control izquierdo"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # === CONEXIÓN ===
        conn_group = QGroupBox("🔌 Conexión Arduino")
        conn_layout = QVBoxLayout(conn_group)
        
        # Puerto
        puerto_layout = QHBoxLayout()
        puerto_layout.addWidget(QLabel("Puerto:"))
        self.puerto_combo = QComboBox()
        self.puerto_combo.addItems(['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8'])
        self.puerto_combo.setCurrentText('COM7')
        puerto_layout.addWidget(self.puerto_combo)
        conn_layout.addLayout(puerto_layout)
        
        # Botones de conexión
        self.btn_conectar = QPushButton("🚀 Conectar")
        self.btn_conectar.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        self.btn_conectar.clicked.connect(self.conectar_arduino)
        
        self.btn_desconectar = QPushButton("🛑 Desconectar")
        self.btn_desconectar.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px;")
        self.btn_desconectar.clicked.connect(self.desconectar_arduino)
        self.btn_desconectar.setEnabled(False)
        
        conn_layout.addWidget(self.btn_conectar)
        conn_layout.addWidget(self.btn_desconectar)
        
        layout.addWidget(conn_group)
        
        # === ESTADÍSTICAS EN VIVO ===
        stats_group = QGroupBox("📊 Estadísticas en Vivo")
        stats_layout = QVBoxLayout(stats_group)
        
        # Labels para estadísticas
        self.lbl_humedad_actual = QLabel("💧 Humedad: -- %")
        self.lbl_temp_actual = QLabel("🌡️ Temperatura: -- °C")
        self.lbl_total_riegos = QLabel("🚿 Total Riegos: 0")
        self.lbl_ultimo_riego = QLabel("⏰ Último Riego: --")
        self.lbl_estado_bomba = QLabel("⚡ Bomba: OFF")
        
        # Estilo para labels
        label_style = "font-size: 12px; padding: 5px; background-color: #ecf0f1; border-radius: 5px; margin: 2px;"
        for label in [self.lbl_humedad_actual, self.lbl_temp_actual, self.lbl_total_riegos, 
                     self.lbl_ultimo_riego, self.lbl_estado_bomba]:
            label.setStyleSheet(label_style)
            stats_layout.addWidget(label)
        
        layout.addWidget(stats_group)
        
        # === CONTROLES ===
        control_group = QGroupBox("🎛️ Controles")
        control_layout = QVBoxLayout(control_group)
        
        self.btn_exportar_csv = QPushButton("💾 Exportar Datos CSV")
        self.btn_exportar_csv.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold; padding: 8px;")
        self.btn_exportar_csv.clicked.connect(self.exportar_datos_csv)
        
        self.btn_exportar_imagen = QPushButton("🖼️ Exportar Gráficos")
        self.btn_exportar_imagen.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 8px;")
        self.btn_exportar_imagen.clicked.connect(self.exportar_graficos_imagen)
        
        self.btn_limpiar = QPushButton("🗑️ Limpiar Datos")
        self.btn_limpiar.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold; padding: 8px;")
        self.btn_limpiar.clicked.connect(self.limpiar_datos)
        
        control_layout.addWidget(self.btn_exportar_csv)
        control_layout.addWidget(self.btn_exportar_imagen)
        control_layout.addWidget(self.btn_limpiar)
        
        layout.addWidget(control_group)
        
        # === LOG DE EVENTOS ===
        log_group = QGroupBox("📝 Log de Eventos")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: monospace;")
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # Spacer
        layout.addStretch()
        
        return panel
    
    def crear_menu(self):
        """Crea la barra de menú"""
        menubar = self.menuBar()
        
        # Menú Archivo
        archivo_menu = menubar.addMenu('📁 Archivo')
        
        exportar_csv_action = QAction('💾 Exportar Datos CSV', self)
        exportar_csv_action.triggered.connect(self.exportar_datos_csv)
        archivo_menu.addAction(exportar_csv_action)
        
        exportar_img_action = QAction('🖼️ Exportar Gráficos', self)
        exportar_img_action.triggered.connect(self.exportar_graficos_imagen)
        archivo_menu.addAction(exportar_img_action)
        
        archivo_menu.addSeparator()
        
        salir_action = QAction('❌ Salir', self)
        salir_action.triggered.connect(self.close)
        archivo_menu.addAction(salir_action)
        
        # Menú Ver
        ver_menu = menubar.addMenu('👁️ Ver')
        
        actualizar_action = QAction('🔄 Actualizar Gráficos', self)
        actualizar_action.triggered.connect(self.actualizar_graficos_manual)
        ver_menu.addAction(actualizar_action)
        
        # Menú Ayuda
        ayuda_menu = menubar.addMenu('❓ Ayuda')
        
        # Acción para Documentación
        documentacion_action = QAction('📚 Documentación', self)
        documentacion_action.triggered.connect(self.abrir_documentacion)
        ayuda_menu.addAction(documentacion_action)
        
        # Separador
        ayuda_menu.addSeparator()
        
        # Acción para Acerca de
        acerca_action = QAction('ℹ️ Acerca de', self)
        acerca_action.triggered.connect(self.mostrar_acerca_de)
        ayuda_menu.addAction(acerca_action)
    
    def setup_statusbar(self):
        """Configura la barra de estado"""
        self.statusbar = self.statusBar()
        self.statusbar.showMessage('🔴 Desconectado - Listo para conectar')
        
    def conectar_arduino(self):
        """Conecta con el Arduino"""
        puerto = self.puerto_combo.currentText()
        
        try:
            self.collector_thread = DataCollectorThread(puerto)
            self.collector_thread.data_updated.connect(self.actualizar_datos)
            self.collector_thread.status_updated.connect(self.actualizar_status)
            self.collector_thread.error_occurred.connect(self.mostrar_error)
            
            self.collector_thread.start()
            
            self.btn_conectar.setEnabled(False)
            self.btn_desconectar.setEnabled(True)
            self.puerto_combo.setEnabled(False)
            
            self.agregar_log(f"🔄 Conectando a {puerto}...")
            
        except Exception as e:
            self.mostrar_error(f"Error de conexión: {str(e)}")
    
    def desconectar_arduino(self):
        """Desconecta del Arduino"""
        if self.collector_thread:
            self.collector_thread.stop()
            self.collector_thread.wait()
            
        self.btn_conectar.setEnabled(True)
        self.btn_desconectar.setEnabled(False)
        self.puerto_combo.setEnabled(True)
        
        self.statusbar.showMessage('🔴 Desconectado')
        self.agregar_log("🛑 Desconectado del Arduino")
    
    def actualizar_datos(self, datos):
        """Actualiza la interface con nuevos datos"""
        self.datos_actuales = datos
        
        # Actualizar estadísticas
        if datos['humedad']:
            ultimo_humedad = datos['humedad'][-1]['valor']
            self.lbl_humedad_actual.setText(f"💧 Humedad: {ultimo_humedad}%")
            
            # Color según nivel de humedad
            if ultimo_humedad < 30:
                color = "#e74c3c"  # Rojo
            elif ultimo_humedad < 45:
                color = "#f39c12"  # Naranja
            else:
                color = "#27ae60"  # Verde
                
            self.lbl_humedad_actual.setStyleSheet(f"font-size: 12px; padding: 5px; background-color: {color}; color: white; border-radius: 5px; margin: 2px; font-weight: bold;")
        
        if datos['temperatura']:
            ultima_temp = datos['temperatura'][-1]['valor']
            self.lbl_temp_actual.setText(f"🌡️ Temperatura: {ultima_temp:.1f}°C")
        
        self.lbl_total_riegos.setText(f"🚿 Total Riegos: {datos['estadisticas']['total_riegos']}")
        
        # Actualizar último riego
        if datos['estadisticas']['ultimo_riego']:
            self.lbl_ultimo_riego.setText(f"⏰ Último Riego: {datos['estadisticas']['ultimo_riego']}")
        
        # Actualizar gráficos
        self.graficos_widget.actualizar_graficos(datos)
    
    def actualizar_status(self, mensaje):
        """Actualiza la barra de estado"""
        self.statusbar.showMessage(f"🟢 {mensaje}")
        self.agregar_log(mensaje)
    
    def mostrar_error(self, error):
        """Muestra errores"""
        self.statusbar.showMessage(f"🔴 Error: {error}")
        self.agregar_log(f"❌ ERROR: {error}")
        QMessageBox.critical(self, "Error", error)
    
    def agregar_log(self, mensaje):
        """Agrega mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {mensaje}")
        
        # Mantener solo últimas 100 líneas
        lines = self.log_text.toPlainText().split('\n')
        if len(lines) > 100:
            self.log_text.setPlainText('\n'.join(lines[-100:]))
    
    def abrir_documentacion(self):
        """Abre la documentación en el navegador web"""
        url = "https://drive.google.com/drive/folders/1n4VyhmAKXzNoXf1zJKcowexxXSsHSj7Q?usp=drive_link"
        try:
            # Intentar con webbrowser
            import webbrowser
            webbrowser.open(url)
            self.agregar_log("📚 Documentación abierta en el navegador")
        except Exception as e:
            try:
                # Alternativa con QDesktopServices
                QDesktopServices.openUrl(QUrl(url))
                self.agregar_log("📚 Documentación abierta en el navegador")
            except Exception as e2:
                # Si ambos fallan, mostrar mensaje con URL
                QMessageBox.information(self, "Documentación", 
                                      f"No se pudo abrir automáticamente.\n\n"
                                      f"Accede manualmente a:\n{url}")
                self.agregar_log(f"❌ Error abriendo documentación: {str(e)}")
    
    def exportar_datos_csv(self):
        """Exporta datos a CSV"""
        if not self.datos_actuales:
            QMessageBox.warning(self, "Advertencia", "No hay datos para exportar")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar Datos CSV", 
                                                f"riego_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                                                "CSV Files (*.csv)")
        
        if filename:
            try:
                # Crear DataFrame con todos los datos
                datos_export = []
                
                # Combinar datos de humedad y temperatura
                max_len = max(len(self.datos_actuales.get('humedad', [])), 
                             len(self.datos_actuales.get('temperatura', [])))
                
                for i in range(max_len):
                    fila = {}
                    
                    # Datos de humedad
                    if i < len(self.datos_actuales.get('humedad', [])):
                        fila['timestamp'] = self.datos_actuales['humedad'][i]['timestamp']
                        fila['humedad'] = self.datos_actuales['humedad'][i]['valor']
                    else:
                        fila['humedad'] = None
                    
                    # Datos de temperatura
                    if i < len(self.datos_actuales.get('temperatura', [])):
                        if 'timestamp' not in fila:
                            fila['timestamp'] = self.datos_actuales['temperatura'][i]['timestamp']
                        fila['temperatura'] = self.datos_actuales['temperatura'][i]['valor']
                    else:
                        fila['temperatura'] = None
                    
                    datos_export.append(fila)
                
                df = pd.DataFrame(datos_export)
                df.to_csv(filename, index=False)
                
                QMessageBox.information(self, "Éxito", f"Datos CSV exportados a:\n{filename}")
                self.agregar_log(f"💾 Datos CSV exportados: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error exportando CSV: {str(e)}")
    
    def exportar_graficos_imagen(self):
        """Exporta gráficos como imagen"""
        if not self.datos_actuales:
            QMessageBox.warning(self, "Advertencia", "No hay datos para exportar")
            return
        
        # Opciones de formato
        formatos = {
            "PNG (*.png)": "png",
            "JPEG (*.jpg)": "jpg", 
            "PDF (*.pdf)": "pdf",
            "SVG (*.svg)": "svg"
        }
        
        filename, formato_seleccionado = QFileDialog.getSaveFileName(
            self, "Guardar Gráficos", 
            f"graficos_riego_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            ";;".join(formatos.keys())
        )
        
        if filename:
            try:
                # Determinar formato
                extension = formatos.get(formato_seleccionado, "png")
                
                # Asegurar que el archivo tenga la extensión correcta
                if not filename.lower().endswith(f'.{extension}'):
                    filename = f"{filename}.{extension}"
                
                # Exportar
                if self.graficos_widget.exportar_imagen(filename):
                    QMessageBox.information(self, "Éxito", 
                                          f"Gráficos exportados como imagen:\n{filename}")
                    self.agregar_log(f"🖼️ Gráficos exportados: {filename}")
                else:
                    QMessageBox.critical(self, "Error", "Error al exportar la imagen")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error exportando imagen: {str(e)}")
    
    def limpiar_datos(self):
        """Limpia todos los datos"""
        reply = QMessageBox.question(self, "Confirmar", "¿Limpiar todos los datos?", 
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.datos_actuales = {}
            self.graficos_widget.figure.clear()
            self.graficos_widget.canvas.draw()
            
            # Resetear labels
            self.lbl_humedad_actual.setText("💧 Humedad: -- %")
            self.lbl_temp_actual.setText("🌡️ Temperatura: -- °C")
            self.lbl_total_riegos.setText("🚿 Total Riegos: 0")
            self.lbl_ultimo_riego.setText("⏰ Último Riego: --")
            self.lbl_estado_bomba.setText("⚡ Bomba: OFF")
            
            # Resetear estilo de humedad
            label_style = "font-size: 12px; padding: 5px; background-color: #ecf0f1; border-radius: 5px; margin: 2px;"
            self.lbl_humedad_actual.setStyleSheet(label_style)
            
            self.agregar_log("🗑️ Datos limpiados")
    
    def actualizar_graficos_manual(self):
        """Actualiza gráficos manualmente"""
        if self.datos_actuales:
            self.graficos_widget.actualizar_graficos(self.datos_actuales)
            self.agregar_log("🔄 Gráficos actualizados manualmente")
        else:
            QMessageBox.information(self, "Info", "No hay datos para mostrar")
    
    def mostrar_acerca_de(self):
        """Muestra información sobre la aplicación"""
        QMessageBox.about(self, "Acerca de", 
                         """🌱 Sistema de Riego Automático
                         
Versión: 2.1 Professional
Desarrollado con PyQt5 + Matplotlib

Características:
• Monitoreo en tiempo real
• Gráficos interactivos
• Exportación de datos CSV
• Exportación de gráficos (PNG, JPG, PDF, SVG)
• Interface profesional
• Documentación integrada

© 2024 - Sistema de Riego Inteligente""")
    
    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        if self.collector_thread and self.collector_thread.isRunning():
            reply = QMessageBox.question(self, "Salir", 
                                       "¿Cerrar aplicación y detener recolección?",
                                       QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.desconectar_arduino()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    """Función principal"""
    app = QApplication(sys.argv)
    
    # Configurar estilo de la aplicación
    app.setStyle('Fusion')
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar aplicación
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()