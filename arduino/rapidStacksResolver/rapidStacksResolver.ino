/*
   C - Start calibration routine
   K - End calibration routine
   E - Echo current settings
   P - Echo current ADC values
   T - Set travel distance (integer nanometers; input long as T XXXXXXXX\n)
   Z - Zero encoder positions to current position

   *  Serial requires 9600 baud, newline characters only for line feed
*/

# include <stdio.h>
# include <math.h>

// Serial variables
String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
long readVal = 0;

// Acquisition details
float distanceStep = 1.5; // Step size in µm
const float stepPeriod = 2.0; // Step period in µm, defined by encoder
const float twoPi = 6.2831853;
float angStep;
int aZero = 0;
int bZero = 0;
int triggerPulseLength = 3; // milliseconds
boolean volatile isCalibrating = false;
int aNext = 0;
int bNext = 0;
boolean aDir = true;
boolean bDir = true;
int dirCase = 0;
const int calibrateTimeout = 10000;

// Pin assignment
int a0 = 3;
int a1 = 1;
int b0 = 2;
int b1 = 0;
int Camtrigger = 3;
int LEDtrigger = 4;

// Initialize variables
int a0val = 0;
int a1val = 0;
int b0val = 0;
int b1val = 0;
int aDiff = 0;
int bDiff = 0;

// aMax, aMin, bMax, bMin;
int maxMin[] = {100, -100, 100, -100};

long aAvg = 0;
long bAvg = 0;

int nSamp = 0;
int nTime = 0;
unsigned long time;

float currAng = 0;

#define FASTADC 1
// defines for setting and clearing register bits
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

void setup() {

#if FASTADC
  // set prescale to 16
  sbi(ADCSRA, ADPS2) ;
  cbi(ADCSRA, ADPS1) ;
  cbi(ADCSRA, ADPS0) ;
#endif

  analogReference(EXTERNAL);

  Serial.begin(9600);
  inputString.reserve(200);

  pinMode(a0, INPUT);
  pinMode(a1, INPUT);
  pinMode(b0, INPUT);
  pinMode(b1, INPUT);

  pinMode(Camtrigger, OUTPUT);
  pinMode(LEDtrigger, OUTPUT);

  // Read initial angle value
  // Record as offset for aAvg and bAvg
  zeroEncoders();

  // Calculate next set value based on distance + current position
  calcAngStep();
  nextStepValues();

  Serial.println("Arduino Resolver ready.");

}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

void loop() {

  if (Serial.available() > 0) {
    serialIncoming();
    char firstChar = inputString.charAt(0);
    // Switch on character value
    switch (firstChar) {

      // Call calibration
      case ('C') :
        Serial.println("Calibrate inputs");
        isCalibrating = true;
        calibrateADCvals();
        break;


      // End calibration
      case ('K') :
        Serial.println("End calibration");
        isCalibrating = false;
        break;

      // Set zero position on encoders
      case ('Z') :
        Serial.println("Zero encoders");
        zeroEncoders();

        break;

      // Set travel distance to trigger on
      case ('T') :
          Serial.println("Set trigger distance");
        //  Serial.println(inputString);
          serialInputToLong();
          distanceStep = float(readVal)/1000;
          Serial.print("Trigger distance set to ");
          Serial.print(distanceStep, 3);
          Serial.println(" µm");
          calcAngStep();
          nextStepValues();
          break;

      case ('P') :
          a0val = analogRead(a0);
          a1val = analogRead(a1);
          b0val = analogRead(b0);
          b1val = analogRead(b1);

        currAng = calcAngleNow();

        Serial.println("Current ADC Values");
        Serial.print("A : ");
        Serial.println(a0val - a1val);
        Serial.print("B : ");
        Serial.println(b0val - b1val);
        Serial.print("angNow : ");
        Serial.println(currAng);
        break;


      // Echo current settings
      case ('E') :
        Serial.println("Echo settings");
        Serial.println("Acquisition settings :");

        Serial.print("Trigger distance : ");
        Serial.print(distanceStep);
        Serial.println(" µm");

        Serial.print("Zero ADC : ");
        Serial.print(aZero);
        Serial.print(" , ");
        Serial.println(bZero);

        Serial.print("Next ADC : ");
        Serial.print(aNext);
        Serial.print(" , ");
        Serial.println(bNext);

        Serial.print("Direction case : ");
        Serial.println(dirCase);

        Serial.print("ADC max/min : ");
        for (int i = 0; i < 4; i++)
        {
          Serial.print(maxMin[i]);
          if (i < 3) {
            Serial.print(", ");
          }
          else {
            Serial.println(" ");
          }
        }

        break;


    }


  }
  

  inputString = "";
  stringComplete = false;

  if (nSamp < 2) {
    a0val = analogRead(a0);
    a1val = analogRead(a1);
    b0val = analogRead(b0);
    b1val = analogRead(b1);
  
    aDiff = a0val - a1val;
    bDiff = b0val - b1val;

  
    aAvg = aAvg + aDiff;
    bAvg = bAvg + bDiff;
    nSamp++;
  //Serial.println(nSamp);
    
  }

  else { 
     nSamp = 0;
     //  aAvg = aAvg >> 1;
     //  bAvg = bAvg >> 1;

//       Serial.print(aAvg);
//       Serial.print(", ");
//       Serial.println(bAvg); 

    // Check if distance travelled is sufficient to trigger

    switch (dirCase) {
      case 1 :
        // Both A and B increase
        if ((aAvg > aNext) and (bAvg > bNext)) {
          triggerAction();
        }
//        else {
//                    Serial.println((aAvg > aNext));
//                    Serial.println((bAvg > bNext));
//        }

        aAvg = 0;
        bAvg = 0;
        break;

      case 2 :
        // A increase, B decrease
        if ((aAvg > aNext) and (bAvg < bNext)) {
          triggerAction();
        }
//        else {
//                    Serial.println((aAvg > aNext));
//          Serial.println((bAvg < bNext));
//        }
        aAvg = 0;
        bAvg = 0;
        break;

      case 3 :
        // A decrease, B increase
        if ((aAvg < aNext) and (bAvg > bNext)) {
          triggerAction();
        }
//        else {
//          Serial.println((aAvg < aNext));
//          Serial.println((bAvg > bNext));
//        }
        aAvg = 0;
        bAvg = 0;
        break;

      case 4 :
        // Both decrease
        if ((aAvg < aNext) and (bAvg < bNext)) {
          triggerAction();
        }
//        else {
//                    Serial.println((aAvg < aNext));
//          Serial.println((bAvg < bNext));
//        }
        aAvg = 0;
        bAvg = 0;
        break;

      
      
    }

  }

}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

float calcAngleNow() {
    
    float aF = (float) (aAvg - maxMin[1]) / (float) (maxMin[0] - maxMin[1]);
    float bF = (float) (bAvg - maxMin[3]) / (float) (maxMin[2] - maxMin[3]);

    float angNow = atan2(aF, bF);

    return angNow;
}

void calibrateADCvals() {

  int calTime = millis();
  inputString = "";
  stringComplete = false;
  Serial.flush();

  while (isCalibrating) {

    if (( millis() - calTime) > calibrateTimeout){
      Serial.println("Calibration timeout");
      isCalibrating = false;
      
    }

    // Collect min-max values for each encoder
    a0val = analogRead(a0);
    a1val = analogRead(a1);
    b0val = analogRead(b0);
    b1val = analogRead(b1);

    aDiff = a0val - a1val;
    bDiff = b0val - b1val;

    if (nSamp < 8) {
      aAvg = aAvg + aDiff;
      bAvg = bAvg + bDiff;
      nSamp++;
    }

    else {

      aAvg = aAvg >> 3;
      bAvg = bAvg >> 3;

      if (aAvg > maxMin[0]) {
        maxMin[0] = aAvg;
      }
      if (aAvg < maxMin[1]) {
        maxMin[1] = aAvg;
      }
      if (bAvg > maxMin[2]) {
        maxMin[2] = bAvg;
      }
      if (bAvg < maxMin[3]) {
        maxMin[3] = bAvg;
      }


      nSamp = 0;
      aAvg = 0;
      bAvg = 0;

      // check to see if a Serial input to stop calibration routine has occured
      if (Serial.available() > 0) {
        serialIncoming();
        char firstChar = inputString.charAt(0);
        if (firstChar == 75) {
          
          Serial.println("Stop calibration");
          isCalibrating = false;
        }
        else{
          inputString = "";
          stringComplete = false;
        }
      }
      

    }
  }
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

void nextStepValues() {
  // Given current step and expected rotation around phase angle, calc
  // encoder readouts for the next step

  float angNow = calcAngleNow(); 
//
//  float aF = (float) (aAvg - maxMin[1]) / (float) (maxMin[0] - maxMin[1]);
//  float bF = (float) (bAvg - maxMin[3]) / (float) (maxMin[2] - maxMin[3]);
//
//  float angNow = atan2(aF, bF);
  float angNext = angNow + angStep;

  aNext = int( (maxMin[0] - maxMin[1])/2 * sin(angNext)) + (maxMin[0] + maxMin[1])/2;
  bNext = int( (maxMin[2] - maxMin[3])/2 * cos(angNext)) + (maxMin[2] + maxMin[3])/2;

  if (aAvg < aNext) {
    aDir = true;
  }
  else {
    aDir = false;
  }

  if (bAvg < bNext) {
    bDir = true;
  }
  else {
    bDir = false;
  }

  if (aDir and bDir) {
    // Both A and B increase
    dirCase = 1;
  }

  if (aDir and not bDir) {
    // A increase, B decrease
    dirCase = 2;
  }

  if (not aDir and bDir) {
    // A decrease, B increase
    dirCase = 3;
  }
 
  if (not aDir and not bDir) {
    // Both decrease
    dirCase = 4;
  }
        

}

void calcAngStep() {

  angStep = twoPi * (distanceStep / stepPeriod);
  
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

void triggerAction() {
 // Serial.println("Trigger!");
  // Fire off a trigger pulse to the camera
  digitalWrite(Camtrigger, HIGH);
  digitalWrite(LEDtrigger, HIGH);
  delay(triggerPulseLength);
  digitalWrite(Camtrigger, LOW);
  digitalWrite(LEDtrigger, LOW);

  // Calc what the next encoder step is to look for
  nextStepValues();
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

void zeroEncoders() {
  // Take a few readings
  nSamp = 0;
  a0val = analogRead(a0);
  a1val = analogRead(a1);
  b0val = analogRead(b0);
  b1val = analogRead(b1);

  aDiff = a0val - a1val;
  bDiff = b0val - b1val;

  while (nSamp < 8) {
    aAvg = aAvg + aDiff;
    bAvg = bAvg + bDiff;
    nSamp++;
  }
  

    // Average over readings and set zero position
    aZero = aAvg >> 2;
    bZero = bAvg >> 2;

    Serial.print("Zero set at :");
    Serial.print(aZero);
    Serial.print(" + ");
    Serial.println(bZero);

    nSamp = 0;
    aAvg = 0;
    bAvg = 0;

    // Set next positions based on this new zero point
    nextStepValues();
  
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

void serialIncoming() {

 // Serial.println("Serial!");
  while (Serial.available()) {
    // get the new byte:
    char inChar = Serial.read();
   // Serial.println(inChar);
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
       stringComplete = true;
     // Serial.println("Input:");
     // Serial.println(inputString);
     Serial.flush();
      /*  Serial.println(inputString);
        Serial.println("Size:");
        Serial.println(inputString.length()-1);
      */
      return true;
    }
    else{
      delay(50);
    }
  }
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

void serialInputToLong() {
        //Serial.println(inputString);
        readVal = 0;
        int digitCount = 0;
        for (int i = 2; i < inputString.length(); i++) {

          if ((inputString[i] >= 48) & (inputString[i] < 58)) {
            readVal = readVal*10;
            readVal = readVal + (inputString[i] - 48);
       // Serial.println(readVal);
            digitCount++;
          } // if is valid ascii numeral
        } // for loop over valid characters

}

