#include <SoftwareSerial.h>

SoftwareSerial BTSerial(10, 11); // RX | TX

int ledR = 3;
int ledG = 5;
int ledB = 6;
char character;
bool ok;
String Data;

void setup() 
{
  Serial.begin(9600);    // 9600 is the default baud rate for the serial Bluetooth module
  BTSerial.begin(9600);
  Serial.print("Ok on commence");
  
}
void loop() 
{

  Data = "";
  ok = false;
  int DataLength = 0;
  bool launch = false;

  String Test = "";

  if (BTSerial.available())
  {
    character = BTSerial.read();
    if (character == 'b')
    {
      while (!ok)
      {
        if (BTSerial.available())
        {
          character = BTSerial.read();
          if (character == 'e')
          {
            ok = true;
          }
          else
          {
            Data.concat(character);
            DataLength++;
          }
        }
      }
    }
  }
  
  // Splitting Data with delimiter ','
  int DataList[3];
  split(DataList, Data.c_str(), DataLength);

  Serial.print("[");
  for (int i = 0; i < 3; i++)
  {
    Serial.print(DataList[i]);
    Serial.print(",");
  }
  Serial.print("]\n");

  int r,g,b;
  r = DataList[0];
  g = DataList[1];
  b = DataList[2];

  blinkLeds(r,g,b);
}

void split(int *tab, char* stringData,int DataLength)
{
  
  String currentStr = "";
  int index = 0;
  for (int i = 0; i < DataLength +1; i++)
  {
    char currentChar = stringData[i];
    if (currentChar == ',' || i == DataLength)
    {
      tab[index] = atoi(currentStr.c_str());
      currentStr = "";
      index++;
    }
    else
    {
      currentStr.concat(currentChar);
    }
  }
  
}

void blinkLeds(int & r, int & g, int & b) 
{
  analogWrite(ledR, r);
  analogWrite(ledG, g);
  analogWrite(ledB, b);
}
