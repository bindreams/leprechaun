Configuration
========================================================================================================================
This page provides reference for ``leprechaun.yml`` - the configuration file Leprechaun uses.
This configuration file needs to be located in your home directory, such as ``C:\Users\User\leprechaun.yml``.

The global structure of the file consists of three optional entries:
  #. ``addresses``, which contains your wallet addresses for mining (see `example <#config-file-example>`_)

The Miner Stack
------------------------------------------------------------------------------------------------------------------------
Leprechaun uses a concept called a "miner stack". When deciding which miner to use for CPU or GPU, it goes through a
list of candidates, and picks the first one that is ready to work.
This list, or stack, is what you specify in your config file:

.. code:: YAML

  cpu-miners:  # This is a miner stack for your CPU
    Miner1:  # This miner is first in line
      currency: XMR
      enabled: false

    Miner2:  # This miner is second in line
      currency: XMR
      condition: when-idle
      idle-time: 5m

    Miner3:  # This miner is third in line
      currency: XMR

In this example, CPU miner stack contains three candidates - ``Miner1``, ``Miner2``, and ``Miner3``. ``Miner1`` is
disabled, and will never be picked to work. ``Miner2`` is enabled, but has a condition that the user needs to be idle
for at least 5 minutes. If this condition is fulfilled, then ``Miner2`` is picked and starts working. Otherwise, or when
the user stops being idle, ``Miner3`` will be picked as the only available option.

If no miners are ready, nothing will be turned on, and the system tray menu will show a status of "No active miners".

The same rules apply to the GPU stack, described in the ``gpu-miners`` entry. If your CPU or GPU stack does not have
any miners, you can simply delete the entry completely from your config file.

General Miner Properties
------------------------------------------------------------------------------------------------------------------------
.. code:: YAML

  example-miner:
    currency: XMR
    enabled: false
    address: "a0bcd1234efgh5678"
    extra-backend-args: ["--argname", "-a", "12"]

A single miner, regardless of type, has the following properties:

.. list-table::
  :widths: 22 20 58
  :header-rows: 1

  * - Field
    - Type
    - Description
  * - ``currency``
    - string
    - Currency that is being mined. Supported currencies include XMR for CPU, ETH for GPU.
  * - ``address``
    - string (optional)
    - Address for mining. If not specified, Leprechaun will look in the global ``addresses`` entry.
  * - ``enabled``
    - bool (optional)
    - Whether this miner is enabled. If omitted, equals to ``true``. Use this to disable miners without deleting
      them from the config file.
  * - ``extra-backend-args``
    - string or list of strings (optional)
    - Extra CLI arguments to pass to the backend that is being used to mine. Useful if you know what backend this
      currency uses, and want to configure it beyond what Leprechaun offers.

Specific Miner Properties
------------------------------------------------------------------------------------------------------------------------
Miner types are identified by their currency. This section enumerates all custom properties that different miners add
in addition to the general properties.

XMR
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code:: YAML

  weak-miner:
    currency: XMR
    process-priority: 1
    process-threads: max / 2

.. list-table::
  :widths: 20 15 65
  :header-rows: 1

  * - Field
    - Type
    - Description
  * - ``process-priority``
    - number or calculation (optional)
    - Specifies process priority, which directly affects the performance of the miner. Process priority can vary from 0
      (lowest), to 2 (default), to 5 (realtime). Recommended values are from 0 to 3.
  * - ``process-threads``
    - number or calculation (optional)
    - Specifies the amount of CPU threads that this process will use. This option is more or less directly proportional
      to the speed at which the miner will run. Use ``max`` variable to allocate all the threads (default). Use ``min``
      or 1 to allocate 1 thread.

ETH
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code:: YAML

  eth-miner:
    currency: ETH
    backend: ethminer

.. list-table::
  :widths: 15 20 65
  :header-rows: 1

  * - Field
    - Type
    - Description
  * - ``backend``
    - string (optional)
    - Specifies the backend used for mining. Must be either "t-rex" (default) or "ethminer". T-Rex is a closed source
      miner with active support and slightly higher hashrate, but it has a 1% developer fee (not collected by us).
      Ethminer is an open-source miner with a 0% fee, but it is not developed and may break in the future.

Conditions
------------------------------------------------------------------------------------------------------------------------
Additionally, every miner can have a condition that controls its behavior. To do this, add a ``condition`` field with
one of the following conditions:

When-Idle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code:: YAML

  example-miner:
    currency: XMR
    condition: when-idle
    idle-time: 5m + 30s

The ``when-idle`` conditions is satisfied when the user is idle for the amount of time, specified in the ``idle-time``
field. This time is expressed as milliseconds, seconds, minutes, hours or days. For example:

- ``500ms`` - 500 milliseconds;
- ``30s`` - 30 seconds;
- ``10m`` - 10 minutes;
- ``12h`` - 12 hours;
- ``0.5d`` - half a day;
- ``2m + 30s`` - 2 minutes and 30 seconds.

.. note::
  Not all systems can count idle time with less than 1 second precision.

On-Schedule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code:: YAML

  example-miner:
    currency: XMR
    condition: on-schedule
    days: [mon, tue, wed, thu, fri]
    from-time: "18:00"
    until-time: "06:00"

Enables the miner based on the day of the week and/or time of day. This conditions requires one or more of these fields:

.. list-table::
  :widths: 15 20 65
  :header-rows: 1

  * - Field
    - Type
    - Description
  * - ``days``
    - list of strings (optional)
    - Specifies on which days the rule applies. On excluded days the condition is not satisfied. By default all days
      are allowed.
  * - ``from-time``
    - string (optional)
    - Time, from which the miner is allowed to run, in 24H format. Default is "00:00".
  * - ``until-time``
    - string (optional)
    - Time, until which the miner is allowed to run, in 24H format. Default is "00:00". If both ``from-time`` and
      ``until-time`` are omitted, the condition is satisfied at any time on allowed days.

Conditions-And
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code:: YAML

  example-miner:
    currency: XMR
    conditions-and:
      - condition: when-idle
        idle-time: 5m
      - condition: on-schedule
        days: [sat, sun]

Allows you to combine several conditions at once. This meta-condition is satisfied only when all nested conditions are
satisfied. In the example above, ``example-miner`` will only run on weekends AND if the user is AFK for at least 5
minutes.

.. tip::
  ``conditions-and`` can be shortened to just ``conditions``.

Conditions-Or
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code:: YAML

  example-miner:
    currency: XMR
    conditions-or:
      - condition: on-schedule
        days: [mon, tue, wed, thu, fri]
        from-time: "22:00"
        until-time: "06:00"
      - condition: on-schedule
        days: [sat, sun]

Allows you to combine several conditions at once with the "or" logic. This meta-condition is satisfied when at least
one of the nested conditions is satisfied. In the example above, ``example-miner`` will run on weekdays from 22:00 until
06:00, but will run 24 hours on weekends.

.. tip::
  ``conditions-and`` and ``conditions-or`` can be combined infinitely with each other and themselves.

Config File Example
------------------------------------------------------------------------------------------------------------------------
.. literalinclude:: ../../leprechaun/data/leprechaun-template.yml
  :language: YAML