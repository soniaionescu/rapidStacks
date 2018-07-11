# include <stdio.h>
# include <math.h>

// Serial variables
String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete

// Pin assignment
int a0 = 3;
int a1 = 2;
int b0 = 1;
int b1 = 0;

// Initialize variables
int a0val = 0;
int a1val = 0;
int b0val = 0;
int b1val = 0;
int aDiff = 0;
int bDiff = 0;

// aMax, aMin, bMax, bMin;
int maxMin[] = {0,0,0,0};

long aAvg = 0;
long bAvg = 0;

int nSamp = 0;
int nTime = 0;
unsigned long time;

char outString[24];

#define FASTADC 1
// defines for setting and clearing register bits
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif

void setup() {
  
#if FASTADC
 // set prescale to 16
 sbi(ADCSRA,ADPS2) ;
 cbi(ADCSRA,ADPS1) ;
 cbi(ADCSRA,ADPS0) ;
#endif

  analogReference(EXTERNAL);
  
  Serial.begin(57600);

  time = micros();

  // Read initial angle value
  // Record as offset for aAvg and bAvg

  // Calculate next set value based on distance + current position

  // 

}

void loop() {

  if (stringComplete) {

  }
  

  a0val = analogRead(a0);
  a1val = analogRead(a1);
  b0val = analogRead(b0);
  b1val = analogRead(b1);

  aDiff = a0val - a1val;
  bDiff = b0val - b1val;

  if (nSamp < 2){
    aAvg = aAvg + aDiff;
    bAvg = bAvg + bDiff;
    nSamp++;
  }
  else {
    
 //   aAvg = aAvg >> 1;
 //   bAvg = bAvg >> 1;


    nSamp = 0;
    aAvg = 0;
    bAvg = 0;
    
    Serial.print(micros() - time);
    Serial.println(" µsec long.");
    
 }

}

void calibrateADCvals() {

  while isCalibrating {

    
    // Collect min-max values for each encoder 
      a0val = analogRead(a0);
      a1val = analogRead(a1);
      b0val = analogRead(b0);
      b1val = analogRead(b1);
    
      aDiff = a0val - a1val;
      bDiff = b0val - b1val;
    
      if (nSamp < 8){
        aAvg = aAvg + aDiff;
        bAvg = bAvg + bDiff;
        nSamp++;
      }
      
      else {
        
        aAvg = aAvg >> 2;
        bAvg = bAvg >> 2;
    
       if (aAvg > maxMin[0]){
          maxMin[0] = aAvg;
        }
        if (aAvg < maxMin[1]){
          maxMin[0] = aAvg;
        }
        if (bAvg > maxMin[2]){
          maxMin[0] = aAvg;
        }
        if (bAvg < maxMin[3]){
          maxMin[0] = aAvg;
        }
      
      nSamp = 0;
      aAvg = 0;
      bAvg = 0;

      // check to see if a Serial input to stop calibration routine has occured

    }
  }
}

void nextStepValues(int aValNow, int bValNow, int angStep) {
  // Given current step and expected rotation around phase angle, calc 
  // encoder readouts for the next step
}

void calcAngStep(double distanceStep) {
  
}

void triggerAction() {
 // Fire off a trigger pulse to the camera
  
 // Calc what the next encoder step is to look for 
}

