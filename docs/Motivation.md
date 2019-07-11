# Motivation

The Python array computing / data science ecosystem is large and popular, but many of the libraries have inconsistant APIs and don't work easily together. However, settling on a few consistent APIs for the scientific computing world in Python would makes things much simpler, but alone it won’t be enough to move the ecosystem forward. It is true that users would prefer consistent APIs so that they can keep using what is familiar to them. However, different users actually need different languages depending on their domain. For example, you can do many of the same things in Pandas as in NumPy but through completely different functions. One is not better than the other, they just have different ways of understanding the world. We prefer to work in the domain of our task and our background. Also, languages are leaky abstractions and we often need to expose particulars of some other level of computation to the user. For example, when we are dealing with Dask Array with often need to specify the chunk size for our computation. We could say “Dask shouldn’t do this! It is incompatible with the NumPy API!”, but Dask is not always able to infer chunks automatically, so it is important they are able to provide a slightly different API that lets users specify this. The truth is our ecosystem grows organically in many different directions and that is its strength. We are balancing the desire for users to have consistent APIs, the ability to have multiple abstractions for different communities, and the need for library authors to continue innovating.

The issue today is that these three goals are often in conflict and it is often hard to move forward on one without degrading the other two. Our code to provide our APIs is linked very directly with our underlying computation mechanism and our abstractions for thinking about the domain. If we can break apart these pieces, then we can support innovation at these different levels, by different parties, under different development cycles. So we can separate the work of defining “What is the proper NumPy API?” from the work of implementing that API. We want different abstractions for different domains, but we also want to be able to translate between them so that users can pick what suits their needs best. The key is we need a way to describe these boundaries in code so that we can all collaborate on them. Python’s type annotations are a step in the right direction, but do not capture the intricacies of the semantics of these projects. For example, let’s take a look at the `concatenate` function in NumPy, we could describe it with different levels of granularity:

- concatenate is a function on the numpy namespace
- concatenate is a function which takes a number of arrays, and an optional axis and an out parameter
- (ignoring out and None value for axis) concatenate returns a new array with the shape of the original arrays, except the axis they are concatenated on is the sum. To iterate through the new array, you iterate through each array passed in over that axis (need more detail here)

To translate this function into a different language, say the language of TensorFlow, we could use any of these definitions. With the first, we would have to know how to map the arbitrary args and kwargs passed into arange into the correct TensorFlow function. With the second, we would have to handle these two cases, at least we would know what the valid parameters are and maybe their types. For the third, we have to know how to create arbitrary arrays in TensorFlow based on a function mapping indices to values and the shape of the array. We see that all these definitions are actually useful and we would like to be able to describe all of them, so that we can choose what level of API we want to see when we look at a NumPy expression.

This requires us to have a formal way for describing these different semantics and translating between them. Luckily, we are not alone in this task. We can rely on type theory (System F) research on domain specific languages embedded in existing languages ([“Folding Domain-Specific Languages: Deep and Shallow Embeddings”](http://www.cs.ox.ac.uk/publications/publication7584-abstract.html)). The key is we want to map the concepts we need to define these APIs into a way that works nicely in the Python ecosystem and fits how we would like to extend these languages in a distributed manner. `metadsl` is exploring this by using type annotations that are compatible with MyPy and a term replacement system. Type annotations are required so that we know the type returned by a function, given some arguments, without actually executing it. This allows us to separate the definition of functions from their many possible implementations, enabling us to support many different user facing APIs that can translate to each other and to different backends.

This requires first building a base library to support these concepts. Then we can build up support for existing APIs in Python, like NumPy, and translate between them. This would let us have a NumPy compatible API that executes with PyTorch. We could also define optimizations, for things like `(a + b)[10] -> a[10] + b[10]`. These types of optimizations are useful to other libraries as well, we would move to use these in Dask and in Numba. The end goal here is to split these libraries into their separate functionality, all relying on metadsl to define these API boundaries. For example, Dask’s definition of how to define chunked operations on array would be equally applicable to other array backends or to Numba, if it is doing multiprocessing work. In turn, Numba’s Python analysis frontend would be equally applicable to dask, to be able to interpret Python control flow and break it up into chunks. Although this would start outside of the core NumPy codebase, ideally NumPy would be broken up into the definition of its API, that has no C dependendencies, and its default implementation that calls out to different C and fortran libraries. This would also make it easier for other Python language implementations, like PyPy or Python in Webassembly, to target this higher level API for NumPy and translate that, instead of translating the underlying C code.

This also makes room for users who have their own domain they work in and want to design an API around. They can create exactly the abstraction they are comfortable with and keep those separate from the underlying computation. Then, as hardware and software requirements evolve, they can improve the performance of their API by targeting new backends, without changing their user facing API. Metadsl does not create one domain language to rule them all, but just gives users some tools to make it easier to express the domains they care about and translate between them.

To reiterate, we need to provide users with consistent APIs and yet we need to support new ways of executing array computation and new domains. So we need to be able to separate the definition of an API from its execution, so that we can solve this problem in a socially distributed way. The end goal is to encourage collaboration and innovation in the community, by making it easier for users to adopt new libraries, and for library authors to try out new ways to define execution.

## History

`metadsl` comes out of needing to be flexible in how array computing is executed, while giving users a familiar API. We want to be able
to continue innovating as an ecosystem in a way that does not disrupt existing use cases.

We found some interesting work by Lenore Mullin, where [over 30 years ago she formalized the semantics of APL into a Mathematics of Arrays](https://www.researchgate.net/publication/308893116_A_Mathematics_of_Arrays). We wanted to make this accessible for Python users, to allow optimizations as well as translating
complicated expressions (outer product) to simpler ones (indexing and scalar math).

At the same time, deep learning has been driving innovation on array compilers, that target new hardware, like GPUs, or have new optimizations, like [polyhedral compilation](https://github.com/facebookresearch/TensorComprehensions).

We love Python because it can glue together different technologies while providing a pleasant user experience. Ideally, users
can keep using whatever API they are accustomed, and be able to execute it with different optimizations on different frameworks.
The Mathematics of Arrays can help by reducing the scope a backend needs to support, by replacing more complex operations with simpler ones.

So we didn't set out to build a DSL creation library in Python, it just turned out
to be what we needed to fulfill these requirements. We needed a way to represent
array operations in a way that is abstracted from their implementation, so that
we could transform them as we like before we translate them to certain backend
to execute. We started by building on top of the
[MatchPy](https://matchpy.readthedocs.io/en/latest/)
library in Python for pattern matching, but after a couple of working versions using that, we found it less complicated
to just build what we needed from the ground up.

It is called `metadsl` and not `array-dsl`, because the core machinery that separates intent from execution is not specific to arrays, and is equally applicable to other compute-intensive domains. For example [`Ibis`](https://www.ibis-project.org/) is a
way to execute SQL queries by using a Pandas like API. `metadsl` is meant to be used to these types of systems so that they are extensible by third parties
and can compose with each other. The goal is to enable innovation on different optimization techniques or backends in a decentralized
manner while providing users with a consistent experience.