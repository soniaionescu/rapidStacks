
#define FASTADC 1

// defines for setting and clearing register bits
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif

void setup() {
 int start ;
 int i ;
 
#if FASTADC
 // set prescale to 16
 sbi(ADCSRA,ADPS2) ;
 cbi(ADCSRA,ADPS1) ;
 cbi(ADCSRA,ADPS0) ;
#endif

 Serial.begin(9600) ;
 Serial.print("ADCTEST: ") ;
 start = millis() ;
 for (i = 0 ; i < 1000 ; i++)
   analogRead(0) ;
   analogRead(1) ;
   analogRead(2) ;
   analogRead(3) ;
 Serial.print(millis() - start) ;
 Serial.println(" msec (1000 calls)") ;
}

void loop() {
}
