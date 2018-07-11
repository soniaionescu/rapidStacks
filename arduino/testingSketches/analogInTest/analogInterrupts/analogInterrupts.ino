int marker = 12;   // marker output pin
int aval = 0;      // analog value

void setup() {
  Serial.begin(9600) ;
  pinMode(marker, OUTPUT); // pin = output
  DIDR0 = 0x3F;            // digital inputs disabled
  ADMUX = 0xC3;            // measuring on ADC3, use the internal 1.1 reference
  ADCSRA = 0xAC;           // AD-converter on, interrupt enabled, prescaler = 16
  ADCSRB = 0x40;           // AD channels MUX on, free running mode
  bitWrite(ADCSRA, 6, 1);  // Start the conversion by setting bit 6 (=ADSC) in ADCSRA
  sei();                   // set interrupt flag
}

void loop() {
  Serial.println(aval);
  delay(500);
}

/*** Interrupt routine ADC ready ***/
ISR(ADC_vect) {
  if (ADMUX == 0xC3) 
    {
      ADMUX = 0xC5;
    }
  else {
    ADMUX = 0xC3;
    }
  int aval = ADCL;
  
  bitClear(PORTB, 4); // marker low
  aval = ADCL;        // store lower byte ADC
  aval += ADCH << 8;  // store higher bytes ADC
  bitSet(PORTB, 4);   // marker high
}
