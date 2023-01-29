Usage Examples
=======================================

Below we provide two example scripts that display a typical usage of **freneticlib**.
The first one uses an executor featuring a bicycle model (:class:`.BicycleExecutor`), while the second one
executes using the BeamNG.tech executor (:class:`.BeamNGExecutor`).


Bicycle Executor Example
---------------------------



.. literalinclude:: ../../example.py
  :language: python


BeamNG.tech Executor Example
-------------------------------

Our second example is rather similar to the first one, except that it uses a different simulator.
However, to use the `BeamNG.tech <https://www.beamng.tech/>`_  simulator, we first have to perform some extra steps.

1. First, request a free researcher license from `https://register.beamng.tech <https://register.beamng.tech>`_.
2. Then, download and install the BeamNG.tech according to the instructions emailed to you.
3. Next, download or clone the `SBFT 2023 CPS tool competition pipeline <https://github.com/sbft-cps-tool-competition/cps-tool-competition>`_, which we use as an interface to BeamNG.tech.
4. Specify the required arguments ``cps_pipeline_path``, ``beamng_home`` and ``beamng_user`` in the initialisation of the :class:`.BeamNGExecutor`, like so ::

.. code-block:: python

    BeamNGExecutor(
        representation=...,
        objective=...,
        cps_pipeline_path="~/cps-tool-competition",
        beamng_home="~/Downloads/BeamNG.tech.v0.26.2.0",
        beamng_user="~/BeamNG.tech",
    )

The rest of the code is exactly the same as in the :class:`.BicycleExecutor` example.

.. note::
    Currently, we tested frenetic-lib on Windows using BeamNG.tech v0.26.2.0
    In case you use it on Linux and/or another version of BeamNG.tech, please share your experience with us.

.. literalinclude:: ../../example_beamng.py
  :language: python



