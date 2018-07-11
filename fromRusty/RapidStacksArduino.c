// Pseudocode for RapidStacks Arduino controller
//
// PC to USB as COM port
// Camera trigger on TTL pin
// Encoder on buffered analog input pin pair

# include <Serial.h>
# include <math.h>

const int Apin = A0;
volatile int a;
const int Bpin = A1;
volatile int b;
volatile double phase = 0;

bool expLatch = FALSE;

const int camPin = D2;
const int camDeadTime = 200 // microseconds

volatile int nSteps = 0; 
volatile int stepSize = 280; // in nanometers
volatile long lastStep = 0; // in nanometers

volatile long encPost = 0; // in nanometers
volatile long encRead = 0; // in nanometers
volatile long lastEncPost = 0; // in nanometers
const long encoderRange = 2000; // in nanometers

void setup() {
	
	analogReference(INTERNAL1V1); // value in 0-1 V. Set to 0-1v1 range for best resolution
	
	Serial.begin(57600);
	while (!Serial) {
		;
	}
	
	digitalWrite(camPin, LOW);
	
}


void loop() {
	
	if (Serial.available()) {
		serRead = Serial.read();
		
		switch serRead {
			
			case 't'
				// Allow experiment to happen
				expLatch = TRUE;
			
			case 'r' 
			
				restOfLine = Serial.getRestOfLine();
				// Set step size to incoming value
				stepSize =  restOfLine;
				
		
			case 'z'
				// Reset counter to 0
				nSteps = 0;
				lastStep = 0;
				
		}

	}
	
	
	if expLatch {
	
		encRead = getEncoderPosition();
		if (lastEncPost > encRead) {
			// Cycled around other end of encoder range
			encPost = encPost + encRead + encoderRange;
		
		}
		else {
			encPost = encPost + encRead;
		}
		
		lastEncPost = encRead;

		if (encPost - lastRead) > stepSize {
			
			// Need to take another image!
			takeImage();
			
			nSteps++
			lastRead = encPost;
		
		}
		
	}
	
	
	
}

int getEncoderPosition() {
	
	// Read encoder position as sine-cosine pair on analog pins
	// Return position value in integer nanometers
	//
	// May need to round off to larger chunk to deal with lack of 
	// gauge precision
	
	a = AnalogRead(Apin);
	b = AnalogRead(Bpin);
	
	phase = (encoderRange)*(Math.atan2(double(a), double(b))/Math.pi + 1)/2;
	
	return int(phase)
	
	
}


void takeImage() {
		
	// Set trigger pin 'high' long enough to take image
	digitalWrite(camPin, HIGH);
	delayMicroseconds(camDeadTime);
	digitalWrite(camPin, LOW);
	
}

