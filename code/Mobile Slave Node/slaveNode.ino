#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <LoRa.h>
/* 
 *  Receiver Side Code
 * 
  Module SX1278 // Arduino UNO/NANO  // Maixduino Silk
    Vcc         ->   3.3V            ->   3.3V          
    MISO        ->   D12             ->   7             
    MOSI        ->   D11             ->   8
    SLCK        ->   D13             ->   9
    Nss         ->   D10             ->   10
    GND         ->   GND             ->   GND
 */
// OLED display width and height, in pixels
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

// Declaration for an SSD1306 display connected to I2C (SDA, SCL pins)
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

int count = 0;
String dataArray[4];  // Array to hold the classified elements
String receivedData;  // Holds the incoming message
String incomingData;
String parsedData[10];      // Array to store the parsed information
int dataCounter = 0;

void setup() {
  // Initialize the Serial Monitor
  Serial.begin(9600);
  // Start OLED display
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    for (;;); // Don't proceed, loop forever
  }
  Serial.println("Oled Started");
  if (!LoRa.begin(433E6)) {  // or 915E6 depending on frequency
    Serial.println("Starting LoRa failed!");
    while (1);
  }

  Serial.println("LoRa Receiver");
  LoRa.setSpreadingFactor(8);
  // Clear the buffer
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.display();
  // Display the information using variables
}


void classifyAndStore(String element) {//Location should have - inbetween
  if (element.indexOf('-') >= 0) {
    dataArray[0] = element;  // Contains '1'
  } else if (element.indexOf('.') >= 0) {//threat severity should have .
    dataArray[1] = element;  // Contains '.'
  } else if (element.length() > 0 && isDigitOnly(element)) {//Node Id should contain only integers
    dataArray[2] = element;  // Integer
  } else if (element.length() > 0 && isAlphaOnly(element)) {//Weapon should only consists of alphabets
    dataArray[3] = element;  // Alphabets only
  }
  else{

  }
}

void loop() {
  int packetSize = LoRa.parsePacket();
  // display.clearDisplay();
  if (packetSize) { 
    // read the packet and store it in `receivedData`
    while (LoRa.available()) {
      receivedData += (char)LoRa.read();
      incomingData +=receivedData;
    }
    if (incomingData.length() > 0) {
        Serial.println("Received: " + incomingData);

        // Split the incoming data by commas
        int startIndex = 0;
        int endIndex = incomingData.indexOf(',');
        while (endIndex >= 0){
          String element = incomingData.substring(startIndex, endIndex);
          Serial.println(element);
          classifyAndStore(element);  // Classify and store the element
          startIndex = endIndex + 1;
          endIndex = incomingData.indexOf(',', startIndex);
        }

        // Handle the last element
        String element = incomingData.substring(startIndex);
        classifyAndStore(element);

        // Output the classified array
        for (int i = 0; i < 4; i++) {
          Serial.print("Array[");
          Serial.print(i);
          Serial.print("]: ");
          Serial.println(dataArray[i]);
        }
        displayInformation(dataArray);
      }
      incomingData="";
  }
}

// Function to parse the received string and store it in the parsedData array
bool isDigitOnly(String str) {
  for (int i = 0; i < str.length(); i++) {
    if (!isdigit(str[i])) return false;
  }
  return true;
}

bool isAlphaOnly(String str) {
  for (int i = 0; i < str.length(); i++) {
    if (!isalpha(str[i])) return false;
  }
  return true;
}


// Function to display the received string array
void displaySerialInformation(String stringArray[4]) {
  Serial.println("Displaying information:");
  for (int i = 0; i < 4; i++) {
    Serial.print("Part ");
    Serial.print(i + 1);
    Serial.print(": ");
    Serial.println(stringArray[i]);
  }
}

// Function to center and display text
void displayInformation(String parsedData[]) {
  display.clearDisplay();  // Clear screen
  drawFullScreenBorder(2);
  drawCornerTriangles(10);
  // Display title at the top
  display.setTextSize(1);
  // Create dynamic strings using the variables
  String node = "Node: " + parsedData[0];
  String severity = "Severity: " + parsedData[1];
  String type = "Type: " + parsedData[2];
  String loc = parsedData[3];

  // Display each string centrally aligned below the title
  display.setTextSize(2);
  displayCenteredText(node, 5);
  display.setTextSize(1);
  displayCenteredText(severity, 23);
  displayCenteredText(type, 33);
  displayCenteredText("Location: ", 43);
  displayCenteredText(loc, 53);

  // Show the result on the display
  display.display();
}

// Function to calculate the center position and display text
void displayCenteredText(String text, int yPos) {
  int16_t x1, y1;
  uint16_t width, height;
  display.getTextBounds(text, 0, yPos, &x1, &y1, &width, &height);// Calculate x-position to center the text
  int16_t xPos = (SCREEN_WIDTH - width) / 2;// Set the cursor to the calculated x and y positions
  display.setCursor(xPos, yPos);
  display.print(text);// Print the text
}


void drawFullScreenBorder(int borderWidth) {// Draw the four borders of the rectangle at the edges of the screen
    display.fillRect(0, 0, SCREEN_WIDTH, borderWidth, SSD1306_WHITE); // Top border
    display.fillRect(0, SCREEN_HEIGHT - borderWidth, SCREEN_WIDTH, borderWidth, SSD1306_WHITE); // Bottom border
    display.fillRect(0, 0, borderWidth, SCREEN_HEIGHT, SSD1306_WHITE); // Left border
    display.fillRect(SCREEN_WIDTH - borderWidth, 0, borderWidth, SCREEN_HEIGHT, SSD1306_WHITE); // Right border
}

void drawCornerTriangles(int triangleSize) {
    display.fillTriangle(0, 0, triangleSize, 0, 0, triangleSize, SSD1306_WHITE);// Top-left triangle
    display.fillTriangle(SCREEN_WIDTH, 0, SCREEN_WIDTH - triangleSize, 0, SCREEN_WIDTH, triangleSize, SSD1306_WHITE);// Top-right triangle
    display.fillTriangle(0, SCREEN_HEIGHT, triangleSize, SCREEN_HEIGHT, 0, SCREEN_HEIGHT - triangleSize, SSD1306_WHITE);// Bottom-left triangle
    display.fillTriangle(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH - triangleSize, SCREEN_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - triangleSize, SSD1306_WHITE);// Bottom-right triangle
}
