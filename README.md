# PyPico

A library for controlling a newport picomotor controller with an external rotary encoder for closed loop operation.

Written by: Matthew Ebert and Josh Cherek

## Dependencies

 * ZeroMQ (for ethernet communication)
 *

## Use

Simple use:

On RPi that is monitoring the encoder angle, run:

```
pypico/server.py
```

On control computer, run:

```
tests/Move2Abs.py -m MOTOR_NUMBER -d DEGREES_TO_MOVE
```

-- or --

```
tests/Move2Abs.py -m MOTOR_NUMBER -s STEPS_TO_MOVE
```

### Command Syntax

 Commands are based off of SCPI command structure which has a tree structure:

```CommandA:CommandB:...:CommandC <Numeric><Unit>```
