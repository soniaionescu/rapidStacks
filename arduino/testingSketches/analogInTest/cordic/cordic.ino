
long cordic_lookup [] = 
{
  0x20000000L,
  0x12E4051EL,
  0x09FB385BL,
  0x051111D4L,
  0x028B0D43L,
  0x0145D7E1L,
  0x00A2F61EL,
  0x00517C55L,
  0x0028BE53L,
  0x00145F2FL,
  0x000A2F98L,
  0x000517CCL,
  0x00028BE6L,
  0x000145F3L,
  0x0000A2FAL,
  0x0000517DL,
  0x000028BEL,
  0x0000145FL,
  0x00000A30L,
  0x00000518L,
  0x0000028CL,
  0x00000146L,
  0x000000A3L,
  0x00000051L,
  0x00000029L,
  0x00000014L,
  0x0000000AL,
  0x00000005L
};

#define ITERS 10000

void setup ()
{
  Serial.begin (57600) ;
  long  elapsed = micros () ;
  for (long i = 0 ; i < ITERS ; i++)
    test_cordic (i << 16, false) ;
  elapsed = micros () - elapsed ;
  Serial.print ("time taken for ") ; Serial.print (ITERS) ;
  Serial.print (" iterations = ") ; Serial.print (elapsed) ; Serial.println ("us") ;
  Serial.print (elapsed / ITERS) ; Serial.println (" us/iter") ;
  test_cordic (0x15555555L, true) ;
  test_cordic (0x95555555L, true) ;
}

void test_cordic (long aa, boolean printres)
{
  long  xx = 607252935L ;
  long  yy = 0L ;

  if ((aa ^ (aa<<1)) < 0L)
  {
    aa += 0x80000000L ;
    xx = -xx ;
    yy = -yy ;
  }
  
  for (int i = 0 ; i <= 10 ; i++)
  {
    long  da = cordic_lookup [i] ;
    long  dx = yy >> i ;
    long  dy = -xx >> i ;
    if (aa < 0L)
    {
      aa += da ;
      xx += dx ;
      yy += dy ;
    }
    else
    {
      aa -= da ;
      xx -= dx ;
      yy -= dy ;
    }
  }
  if (!printres)
    return ;
  Serial.print ("end angle=") ; Serial.print (aa) ;
  Serial.print ("  end x = 0.") ; Serial.print (xx) ;
  Serial.print ("  end y = 0.") ; Serial.println (yy) ;
}

void loop () {
}
