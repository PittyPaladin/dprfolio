+++
title = "A driver for the Ublox M9: IBIT"
date = "2026-03-01"
description = "Article explaining the different working modes. In this specific case, the IBIT."
tags = [
    "gnss",
    "ublox",
    "receiver",
    "driver"
]
+++


## The Initialised Built-In Test (IBIT) procedure
As you may know the driver can, at the user's discretion, initiate a test. It is intended to check that internally the receiver is working properly, and it could take the driver out of Failure mode. This is called IBIT.

Below I list the IBIT procedure I've designed:

1. **Clear memory**: delete all configuration in flash and Battery Backed RAM (BBR), and rebuild configuration. Very similar to step #1 from PBIT (and the message is actually the same, UBX-CFG-CFG, changing the `deviceMask` field), with the difference that this one will erase flash. This will set the receiver to a factory configuration state.

2. If the UBX-CFG-CFG returned and acknowledge (aka it returned a UBX-ACK-ACK), reset your configuration database information. In other words: "you've just reset your receiver's configuration, so reset the knowledge you had about it on your end".

3. **Hard reset the receiver**: reset the receiver as a cold-start, immediately. This will reset previous knowledge on satellite locations, your position, clock parameters, etc. This message is not acknowledged, hence the timer in the code, where you just wait some seconds until it comes back up from the reset. This will disconnect the receiver serial connection, so a call to `connect()` is required.

4. Run a **BIT**. The BIT was explained [here]({{< ref "blog/ubloxM9/pbit" >}}).

5. **Configuration Control**. Same as [PBIT]({{< ref "blog/ubloxM9/pbit" >}}). The reset in configuration rendered all configuration layers to factory. You now need to apply the application-specific configuration to the receiver.

## IBIT transition
IBIT shall transition to Operational mode when all the aforementioned steps are successful. Any step failing or a timeout before completing the procedure will kick the driver to Failure mode.
