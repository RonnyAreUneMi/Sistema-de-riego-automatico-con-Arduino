# 🌱 Sistema de Riego Automático Inteligente

Un sistema completo de riego automático que combina hardware Arduino con una aplicación de monitoreo profesional en Python. Ideal para el cuidado automatizado de plantas con monitoreo en tiempo real y análisis de datos.

## 📋 Características Principales

### 🔧 Hardware (Arduino)
- **Monitoreo automático** de humedad del suelo y temperatura ambiente
- **Control inteligente** de bomba de agua con relé
- **Display LCD** con información en tiempo real y "personalidad" de la planta  
- **Sistema de seguridad** con tiempos máximos de riego y períodos de espera
- **Análisis post-riego** para verificar efectividad del sistema

### 💻 Software (Python + PyQt5)
- **Interfaz gráfica profesional** con paneles de control y monitoreo
- **Gráficos en tiempo real** con matplotlib integrado
- **Exportación de datos** a CSV e imágenes (PNG, JPG, PDF, SVG)
- **Log de eventos** y estadísticas detalladas
- **Comunicación serial** asíncrona con Arduino

## 🛠️ Componentes Hardware

| Componente | Modelo | Pin/Conexión |
|------------|--------|--------------|
| Microcontrolador | Arduino Uno/Nano | - |
| Sensor Humedad Suelo | Analógico | A0 |
| Sensor Temperatura | DHT11 | Pin 9 |
| Display | LCD I2C 16x2 | SDA/SCL (0x27) |
| Relé | 5V/10A | Pin 8 |
| Bomba de Agua | 12V DC | Controlada por relé |

## 📦 Instalación

### Requisitos Arduino
```cpp
// Librerías necesarias
#include <LiquidCrystal_I2C.h>  // Control LCD I2C
#include <DHT.h>                // Sensor DHT11
```

### Requisitos Python
```bash
pip install PyQt5 matplotlib pandas numpy seaborn pyserial
```

### Configuración del Hardware
1. **Conexiones:**
   - Sensor humedad → Pin A0
   - DHT11 → Pin 9 (con resistencia pull-up 10kΩ)
   - LCD I2C → SDA/SCL
   - Relé → Pin 8
   - Bomba → Relé (normalmente abierto)

2. **Calibración del sensor de humedad:**
   ```cpp
   #define SENSOR_SECO 1023    // Valor en aire
   #define SENSOR_MOJADO 300   // Valor en agua
   ```

## 🚀 Uso del Sistema

### 1. Cargar código en Arduino
```bash
# Abrir archivo: sistema_riego_arduino.ino
# Verificar puerto serial y librerías
# Cargar a Arduino Uno/Nano
```

### 2. Ejecutar aplicación Python
```bash
python main_app.py
```

### 3. Configurar conexión
- Seleccionar puerto COM correcto
- Velocidad: 115200 baudios
- Hacer clic en "🚀 Conectar"

## ⚙️ Configuración

### Parámetros de Riego (Arduino)
```cpp
#define UMBRAL_RIEGO 30          // Humedad mínima (%)
#define UMBRAL_SATISFECHO 45     // Humedad objetivo (%)
#define TIEMPO_RIEGO_MAX 10000   // Tiempo máximo riego (ms)
#define tiempoMinEntreriegos 10000 // Espera entre riegos (ms)
```

### Puerto Serial (Python)
```python
# En la interfaz gráfica, seleccionar:
puerto = 'COM7'  # Windows
# puerto = '/dev/ttyUSB0'  # Linux
# puerto = '/dev/cu.usbserial'  # macOS
```

## 📊 Funciones de Monitoreo

### Dashboard en Tiempo Real
- **Humedad actual** con código de colores
- **Temperatura ambiente**
- **Contador de riegos** realizados
- **Timestamp del último riego**
- **Estado de la bomba** (ON/OFF)

### Gráficos Interactivos
- **Humedad vs Tiempo** con umbrales visuales
- **Temperatura histórica**
- **Distribución de humedad** (histograma)
- **Eventos de riego** marcados

### Exportación de Datos
```python
# Formatos disponibles:
- CSV: Datos tabulares para análisis
- PNG/JPG: Gráficos en alta resolución
- PDF: Reportes profesionales
- SVG: Gráficos vectoriales
```

## 🔄 Lógica del Sistema

### Algoritmo de Riego
```
1. Leer humedad del suelo cada 3 segundos
2. Si humedad <= 30%:
   - Activar bomba (si tiempo mínimo cumplido)
   - Monitorear hasta humedad >= 45% o timeout
3. Desactivar bomba y esperar análisis (5 seg)
4. Evaluar efectividad del riego
5. Repetir ciclo
```

### Estados del Sistema
- **🟢 Esperando:** Humedad adecuada, sin acción
- **🟡 Analizando:** Verificando humedad post-riego
- **🔴 Regando:** Bomba activa, aplicando agua
- **⚠️ Urgente:** Humedad crítica (<15%)

## 🎨 Interfaz de Usuario

### Mensajes de la Planta (LCD)
```
Humedad > 80%: "Me ahogo :O"
Humedad 60-80%: "Muy mojada :|"  
Humedad 40-60%: "Estoy feliz :)"
Humedad 30-40%: "Tengo sed :/"
Humedad 15-30%: "Agua urgente :("
Humedad < 15%: "Me muero D:"
```

### Panel de Control (Python)
- **🔌 Conexión:** Selección de puerto y estado
- **📊 Estadísticas:** Métricas en tiempo real
- **🎛️ Controles:** Exportación y limpieza de datos
- **📝 Log:** Historial de eventos del sistema

## 📈 Análisis de Datos

El sistema registra y permite analizar:
- **Patrones de riego** por horas/días
- **Correlación temperatura-humedad**
- **Eficiencia del sistema** de riego
- **Tendencias estacionales** (datos a largo plazo)

## 🛡️ Características de Seguridad

- **Timeout de riego:** Máximo 10 segundos continuos
- **Tiempo entre riegos:** Mínimo 10 segundos de espera
- **Análisis post-riego:** Verificación automática de efectividad
- **Detección de errores:** Sensores y comunicación
- **Modo fail-safe:** Bomba OFF en caso de error

## 🔧 Resolución de Problemas

### Problemas Comunes

#### ❌ "Error de conexión serial"
```bash
# Verificar:
- Cable USB conectado
- Puerto COM correcto
- Arduino encendido
- Drivers instalados
```

#### ❌ "Sensor de temperatura Error"
```bash
# Revisar:
- Conexión DHT11 en pin 9
- Resistencia pull-up 10kΩ
- Alimentación 3.3V/5V
```

#### ❌ "Bomba no activa"
```bash
# Comprobar:
- Conexión relé pin 8
- Alimentación bomba 12V
- Cableado relé (NO/NC)
```

### Debug Mode
```cpp
// En Arduino, habilitar debug completo:
Serial.print("Raw sensor: ");
Serial.print(sensorValue);
Serial.print(" -> Humedad: ");
Serial.print(humedad);
```

## 📄 Estructura del Proyecto

```
sistema-riego-automatico/
├── README.md
├── arduino/
│   ├── sistema_riego_arduino.ino
│   └── libraries/
│       ├── LiquidCrystal_I2C/
│       └── DHT/
├── python/
│   ├── main_app.py
│   ├── requirements.txt
│   └── exports/
├── docs/
│   ├── esquematico.png
│   ├── conexiones.jpg
│   └── manual_usuario.pdf
└── examples/
    ├── datos_ejemplo.csv
    └── graficos_ejemplo.png
```


## 📞 Soporte
Documentación: Ver documentación completa
Email: rarellanou@unemi.edu.ec
  



**¿Te gustó el proyecto? ⭐ ¡Dale una estrella en GitHub!**

---
*Desarrollado con ❤️ para el cuidado automatizado de plantas*
