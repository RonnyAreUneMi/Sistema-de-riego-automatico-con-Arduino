#include <LiquidCrystal_I2C.h>
#include <DHT.h>

#define DHTPIN 9
#define DHTTYPE DHT11
#define RELE_PIN 8
#define UMBRAL_RIEGO 30
#define UMBRAL_SATISFECHO 45
#define TIEMPO_RIEGO_MAX 10000

#define SENSOR_SECO 1023
#define SENSOR_MOJADO 300

LiquidCrystal_I2C lcd(0x27, 16, 2);
DHT dht(DHTPIN, DHTTYPE);

unsigned long ultimoRiego = 0;
unsigned long tiempoMinEntreriegos = 10000;
unsigned long tiempoAnalisis = 5000;
bool bombaActiva = false;
bool plantaQuiereAgua = false;
bool analizandoHumedad = false;
unsigned long inicioRiego = 0;
unsigned long inicioAnalisis = 0;

void setup() {
  Serial.begin(115200);
  
  pinMode(RELE_PIN, OUTPUT);
  digitalWrite(RELE_PIN, HIGH);
  bombaActiva = false;
  
  lcd.init();
  delay(200);
  lcd.backlight();
  
  dht.begin();
  
  lcd.setCursor(0, 0);
  lcd.print("Sistema de Riego");
  lcd.setCursor(0, 1);
  lcd.print("Iniciando...    ");
  delay(2000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Bomba: OFF      ");
  lcd.setCursor(0, 1);
  lcd.print("Riego no necesar");
  delay(2000);
  lcd.clear();
  
  Serial.println("=== Sistema de riego iniciado ===");
  Serial.println("Estado inicial: Bomba OFF - Riego no necesario");
  ultimoRiego = 0;
}

void loop() {
  int sensorValue = analogRead(A0);
  
  int humedad = map(sensorValue, SENSOR_SECO, SENSOR_MOJADO, 0, 100);
  humedad = constrain(humedad, 0, 100);
  
  float temperatura = dht.readTemperature();
  
  verificarDeseoAgua(humedad);
  controlarRiego(humedad);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Tu planta dice:");
  lcd.setCursor(0, 1);
  if (humedad > 80) {
    lcd.print("Me ahogo :O");
  } else if (humedad > 60) {
    lcd.print("Muy mojada :|");
  } else if (humedad > 40) {
    lcd.print("Estoy feliz :)");
  } else if (humedad > 30) {
    lcd.print("Tengo sed :/");
  } else if (humedad > 15) {
    lcd.print("Agua urgente :(");
  } else {
    lcd.print("Me muero D:");
  }
  delay(3000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Temp: ");
  if (isnan(temperatura)) {
    lcd.print("Error");
  } else {
    lcd.print(temperatura, 1);
    lcd.print("C");
  }
  
  lcd.setCursor(0, 1);
  lcd.print("Humedad: ");
  lcd.print(humedad);
  lcd.print("%");
  delay(3000);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  if (bombaActiva) {
    lcd.print("Bomba ON");
    lcd.setCursor(0, 1);
    lcd.print("Regando...");
  } else if (analizandoHumedad) {
    lcd.print("Analizando");
    lcd.setCursor(0, 1);
    lcd.print("humedad espere");
  } else {
    lcd.print("Riego no");
    lcd.setCursor(0, 1);
    lcd.print("necesario");
  }
  
  Serial.print("Raw sensor: ");
  Serial.print(sensorValue);
  Serial.print(" -> Humedad: ");
  Serial.print(humedad);
  Serial.print("% | Temp: ");
  Serial.print(temperatura);
  Serial.print("C | Estado: ");
  if (bombaActiva) {
    Serial.print("RIEGO ACTIVO");
  } else {
    Serial.print(plantaQuiereAgua ? "RIEGO NO NECESARIO" : "ESPERANDO");
  }
  Serial.print(" | Planta necesita agua: ");
  Serial.println(plantaQuiereAgua ? "SI" : "NO");
  
  delay(3000);
}

void verificarDeseoAgua(int humedad) {
  if (humedad <= UMBRAL_RIEGO) {
    plantaQuiereAgua = true;
  } else if (humedad >= UMBRAL_SATISFECHO) {
    plantaQuiereAgua = false;
  }
}

void controlarRiego(int humedad) {
  unsigned long tiempoActual = millis();
  
  if (analizandoHumedad) {
    if (tiempoActual - inicioAnalisis >= tiempoAnalisis) {
      analizandoHumedad = false;
      Serial.println("Análisis completado");
      
      if (humedad <= UMBRAL_RIEGO) {
        plantaQuiereAgua = true;
        Serial.println("Resultado: Aún necesita más riego");
      } else {
        plantaQuiereAgua = false;
        Serial.println("Resultado: Riego suficiente");
      }
    }
    return;
  }
  
  if (bombaActiva) {
    if (!plantaQuiereAgua || humedad >= UMBRAL_SATISFECHO || 
        (tiempoActual - inicioRiego >= TIEMPO_RIEGO_MAX)) {
      
      digitalWrite(RELE_PIN, HIGH);
      bombaActiva = false;
      ultimoRiego = tiempoActual;
      
      analizandoHumedad = true;
      inicioAnalisis = tiempoActual;
      
      if (humedad >= UMBRAL_SATISFECHO) {
        Serial.println("Planta satisfecha - Bomba OFF - Iniciando análisis");
      } else {
        Serial.println("Tiempo máximo alcanzado - Bomba OFF - Iniciando análisis");
      }
    }
    return;
  }
  
  if (plantaQuiereAgua && humedad <= UMBRAL_RIEGO) {
    if (tiempoActual - ultimoRiego >= tiempoMinEntreriegos) {
      Serial.println("Riego necesario - Activando bomba");
      
      delay(100);
      digitalWrite(RELE_PIN, LOW);
      bombaActiva = true;
      inicioRiego = tiempoActual;
      
      Serial.print("Riego iniciado - Humedad: ");
      Serial.print(humedad);
      Serial.println("% - Regando");
    } else {
      Serial.println("Riego necesario pero esperando tiempo entre riegos");
    }
  }
}