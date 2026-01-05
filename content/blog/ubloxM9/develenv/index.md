+++
title = "A driver for the Ublox M9: Development environment"
date = "2025-12-28"
description = "Article explaining the development environment of a driver project for a commercial GNSS receiver."
tags = [
    "gnss",
    "ublox",
    "receiver",
    "driver"
]
+++


## Hardware set up

As mentioned in the last post:
* Antenna positioned in the most open area possible. I live in the 3rd floor of a building so 20 cm sticking out from the window was the best I could do. This will yield quite a lot of multipath[^1] but will make do. Connect the SMA male connector of the antenna into the SMA female of the Sparkfun board.
* USB-C data-capable cable connected to the Sparkfun board.

[^1]: Multipath is the reflection of the satellite signal before reaching the receiver (bouncing through the building walls in this case), thus arrival times larger than an actual line of sight would.

## Software set up

Being Python the programming language of choice, create a virtual environment to avoid polluting the base installation. You may use `pip`, but I used `conda` like so:

```console
conda create --name myEnvName python=3.11
conda activate myEnvName
```

Then proceed to install the only third-party dependency of this project, `pyserial`, which will abstract and encapsulate all serial port functionality and be OS-independent.

```console
conda install -c conda-forge pyserial
```

If it's your first time hearing about `pyserial` I first recommend playing with its main methods, and perhaps reading some traces like the NMEA messages the receiver outputs by default.

From this point on it is assumed some knowledge of the built-in and third-party libraries that I will be mentioning. This will take the shape more of a "look how I did it" than a tutorial.

You can see the code in the Github repo [here](https://github.com/PittyPaladin/ubloxTalker).

### Some notes on the Interface Document

The [Interface Document](https://www.u-blox.com/sites/default/files/u-blox-M9-SPG-4.04_InterfaceDescription_UBX-21022436.pdf) defines two ways receive data from an Ublox receiver: via NMEA and via UBX messages. They are two different types of protocols. The former is used since configuration requires UBX anyway. For details on the UBX protocol take a look at §3.

When looking at the ways to configure the receiver, one would typically look at the messages under the "UBX-CFG (0x06)" section. However, they come with a warning:

> This message is deprecated in protocol versions greater than 23.01. Use UBX-CFG-VALSET, UBX-CFGVALGET, UBX-CFG-VALDEL instead. See the Legacy UBX Message Fields Reference for the corresponding configuration item.

In other words, if you want some future-proofness to your code, use the new configuration interface from §5. Without going into much detail, since it's already in the document, the new interface gives you a key/value pair for each configurable item in existence. This way, one can stack up all configuration key/value pairs in the same message and send it in one go.

## Let's go

### Scope

You can make things as complicated as you want. That applies particularly to GNSS receiver drivers: simple communication parsing NMEA messages and using the default configuration is very easy to do. If you want a more robust driver that handles several operational modes, handles faults and acts upon them, in addition to apply your application-specific config, then that's another story. The scope of the project I'm presenting to you is this second type. As the reader will see, the driver is also oriented towards energy saving.

The capabilities for the M9 GNSS receiver driver are the following:

1. Full operational modes
   1. Powerup Built-In Test (**PBIT**): battery of tests that run when starting up the driver[^2]. Also loads the receiver with application-specific configuration.
   2. Continuous Built-In Test (**CBIT**): launched automatically every X seconds from the first time an **Operational** mode occurs. They interrupt the normal operational mode to do some quick checks to assert the system is running well, and proceed to correct those that can be corrected and resume **Operational**, or to **Failure** if they can't.
   3. Initiated Built-In Test (**IBIT**): BIT mode initiated by the driver instance owner (can only be called upstream). Designed to force a hard reset and a do-over of the **PBIT** mode, when for some unknown reason the driver is not performing as expected.
   4. Operational Mode (**Operational**): normal operational mode in which the driver does its main functions, like provide positioning, geofencing, etc. This state may transition to **Failure** or **CBIT** by itself, or to **IBIT** if asked by the driver instance owner.
   5. Failure Mode (**Failure**): no-return mode that captures the activities of the main `Run` method. If the driver ends up being integrated in a real receiver, this mode could alert upstream of the failure and the caller perhaps invoke an IBIT.
2. Communication with the receiver using the UBX protocol only.
3. Configuration of the receiver using the new interface defined in §5 of the [Interface Document](https://www.u-blox.com/sites/default/files/u-blox-M9-SPG-4.04_InterfaceDescription_UBX-21022436.pdf).

[^2]: The caller program (the one upstream the GNSS driver) does not control power shutdown to the receiver. In a real deployment it should. After powering up the receiver it should wait a few seconds for it to wake up and then go to PBIT mode by calling the main `Run` method.

### Scaffolding

I'm using an object oriented approach. There's a `GNSSDriver` class that encapsulates all attributes it may have and provides all the public methods needed to use it. In Python there's no such thing as "public" and "private" methods as in C++. Everything is public. Still, I like to make the differentiation in the comments (some people add underscores to indicate it).
