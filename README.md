# frenetic-lib

## The Frenetic story
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

### Main features
frenetic helps you to 
- select a road representation (e.g. Bezier, Cartesian, Kappa, Theta),
- define an objective (i.e. road feature to minimise/maximise),
- choose mutation parameters,
- define an executor (i.e. target executor), and
- trigger execution (for a certain time/number of iterations)

Behind the scenes, frenetic will take care of creating random roads (in your specified representation),
followed by a mutation phase with the goal of producing a variety of individual roads 
according to the chosen objective.


### Where will the Frenetic journey go?

In the future, we want to ...

# How to use

Frenetic's main modules are the `Frenetic` and `FreneticCore` classes.
`Frenetic` is responsible for the execution flow, `FreneticCore` 

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

Please also let us know if you used frenetic in your project. 
It always feels good to know a project is used elsewhere. 
