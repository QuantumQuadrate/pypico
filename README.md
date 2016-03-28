# PyPico

A library for controlling a newport picomotor controller with an external rotary encoder for closed loop operation.

Written by: Matthew Ebert and Josh Cherek

## Dependencies

 * ZeroMQ (for ethernet communication)
 *

## Use

### Command Syntax

 Commands are based off of SCPI command structure which has a tree structure:

```CommandA:CommandB:...:CommandC <Numeric><Unit>```
