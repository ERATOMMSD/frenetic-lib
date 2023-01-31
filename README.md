![Python 3.9](https://img.shields.io/badge/python-3.9-blue?logo=python)
[![PyPI](https://img.shields.io/pypi/v/freneticlib)](https://pypi.org/project/freneticlib/)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/ERATOMMSD/frenetic-lib/python-package.yml)
[![Documentation Status](https://readthedocs.org/projects/frenetic-lib/badge/?version=latest)](https://frenetic-lib.readthedocs.io/en/latest/?badge=latest)
[![MIT License](https://img.shields.io/badge/license-MIT-yellow)](https://choosealicense.com/licenses/mit/)

# frenetic-lib

A library for 
- simulation-based automated driving system (ADS) testing, 
- research on road representations, and 
- development of search-based heuristics for road scenario generation.

One of the main components of an automated driving scenario its _road structure_, which can largely affect the ADS's behaviour.
Therefore, research has started investigating the generation of road structures for ADS testing.
However, three main problems in the research on road generation remain:
1. **Various road representations exist** and are reported in literature.
2. **Different search/generation approaches** may be employed in combination with these representations. 
3. Each combination of representation and generation approaches can be applied to **a variety of driving agents and simulators**.

To facilitate this research, we developed **frenetic-lib**. 
frenetic helps in the research on and allows to 
- select a road representation (e.g. Bezier, Cartesian, Kappa, Theta),
- define an objective (i.e. road feature to minimise/maximise),
- specify mutation and crossover parameters,
- select a predefined simulator or define your own executor, and
- trigger a search and run it until a certain stop criterion (time or number of iterations) is met.

The search itself is based on a customised genetic algorithm method, 
and applies two kinds of mutation operators to allow for efficient exploration and goal-driven exploitation.
Behind the scenes, freneticlib takes care of creating an initial random population (in the specified representation),
and automatically switches to the mutation/crossover phase with the goal of producing a variety of individual roads
according to the chosen objective.

For more details refer to the documentation's Architecture page.

### The Frenetic story
Frenetic is a search-based algorithm, originally developed as submission to the
[SBST 2021 Tool Competition](https://sbst21.github.io/program/).
Frenetic was very successful and turned out to be one of the best tools that year.

After the competition, we continued our development of Frenetic and adapted it
for various projects, including research on different road representations.
We noticed however, that the SBST tool pipeline (i.e. the execution flow) is geared specifically towards the competition and limits research versatility.
Hence, it was difficult to integrate a different driving agent or alter the execution routine.

Furthermore, in the 2022 iteration of the SBST competition, we also observed that several competitors built upon Frenetic and its road representation.
Due to its popularity, we decided to extract the "Frenetic-part" of our submission into a standalone library,
so it can be more easily developed, maintained and integrated in other projects.

As a result, we extract Frenetic into this own library. This will support our own research
and allow other people to more easily reuse the code.


# How to use freneticlib

## Installation

You can install frenetic, you can simply call
```
pip install freneticlib
```

To alternatively obtain the latest (non-release) version from Github, use    
`pip install git+https://github.com/ERATOMMSD/frenetic-lib`

**Note:**
There might be an issue with installing the `bezier` library. This is a known problem ().
If you encounter an error stating that 
```
The BEZIER_INSTALL_PREFIX environment variable must be set
```
please install `bezier` first using the following command:
```
BEZIER_NO_EXTENSION=true \
  python  -m pip install --upgrade bezier --no-binary=bezier
```

## Usage Example

freneticlib features two primary classes: `FreneticCore` and `Frenetic`.

- `FreneticCore` is responsible for generation of road representations and the genetic algorithm methodology.
It applies the correct mutation and crossover operators and iteratively yields new roads.

- `Frenetic` on the other hand is the orchestrator of the execution flow. 
It asks `FreneticCore` for new roads and triggers the indivudal roads' simulation. 
Furthermore, it monitors the stop criterion.

### Code Example
Have a look at the [example.py](https://github.com/ERATOMMSD/frenetic-lib/blob/main/example.py) file, which provides a very basic usage example.

Specifically, the code defines several settings, before combining them in the Frenetic class.
1. First, we have to choose which road representation we would like to use. In this case, the `FixStepKappaRepresentation`.
```python
representation = FixStepKappaRepresentation(length=30, variation=5, step=10.0)
```
2. Next, we select an objective to minimise/maximise.
```python
# Setup an objective. Here: maximize the distance_from_center (i.e. push the vehicle off the road)
objective = MaxObjective(
    feature="distance_from_center",
    # every simulation produces 10 records per second, we extract the maximum value of the selected feature 
    per_simulation_aggregator="max",
)
```
3. The FreneticCore class specifies the mutation, exploitation and crossover operators.
```python
# Define the Frenetic core using representation, objective and the mutation operators
core = FreneticCore(
    representation=representation,
    objective=objective,
    mutator=FreneticMutator(),
    exploiter=exploiters.Exploiter([
        exploiters.ReverseTest(),
        exploiters.SplitAndSwap(),
        exploiters.FlipSign()
    ]),
    crossover=crossovers.ChooseRandomCrossoverOperator(size=20),
)
```

4. A Frenetic object is created which orchestrates the execution, triggers the executor and checks for stop criteria.
```python
# Define the Frenetic executor and the stop-criterion.
frenetic = Frenetic(
    core,
    executor=BicycleExecutor(
        representation=representation,
        objective=objective
    ),
    stop_criterion=CountingStop(n_random=50, n_total=250),
)
```

5. Finally, we can start the execution, and subsequently store the results and plot the evolution of the objective's feature value.
```python
# run the search
frenetic.start()

# store the history for later use
frenetic.store_results("./data/history.csv")

# Display the progress
frenetic.plot("./data/plot.png")
```

{% note %}
**Note:** The stop criterium has been set VERY low for showcase purposes. 
In a usual search these values will be several orders of magnitude higher.
{% endnote %}

## Under the Hood

Please refer to the [documentation](https://frenetic-lib.readthedocs.io) for more information on how the classes communicate.


## Reference
For academic publications, please consider the following reference:

E. Castellano, A. Cetinkaya, C. Ho Thanh, Stefan Klikovits, X. Zhang and P. Arcaini. Frenetic at the SBST 2021 Tool Competition. In: Proc. 2021 IEEE/ACM 14th International Workshop on Search-Based Software Testing (SBST). IEEE, 2021.
```bibtex
@InProceedings{Castellano:2021:SBST,
  author={Castellano, Ezequiel and Cetinkaya, Ahmet and Thanh, Cédric Ho and Klikovits, Stefan and Zhang, Xiaoyi and Arcaini, Paolo},
  title={Frenetic at the SBST 2021 Tool Competition},
  booktitle={2021 IEEE/ACM 14th International Workshop on Search-Based Software Testing (SBST)},
  year={2021},
  editor={Jie Zhang and Erik Fredericks},
  pages={36-37},
  publisher={IEEE},
  keywords={genetic algorithms, genetic programming},
  doi={10.1109/SBST52555.2021.00016}
}
```

# Contribute
We are warmly welcoming contributions in various forms.
If you find a bug or want to share an improvement, please don't hesitate to open a new issue.

Please also let us know if you used freneticlib in your project.
It always feels good to know a project is used elsewhere.
