# Simple Build Script Framework (sbsf)

The Simple Build Script Framework (`sbsf`) provides a simple framework to quickly create build scripts in Python. The build scripts may be used for any project of any type.

The resulting build script will have an interface similar to and inspired by [GNU Make](https://www.gnu.org/software/make/manual/make.html).


## Usage & Quickstart

First, you must create a build script using `sbsf`. Below is a sample build script. More examples can be found in the `examples` folder of this repository.

```py
import sys
import sbsf

# Initialize a new 'builder', this will store our targets
builder = sbsf.new_builder()

# Define a target using a function (or lambda, callable class, etc.)
builder.add_target(
    name='build',
    help='Build/compile all necessary files',
    function=lambda ctx: print('Building...'),
)

# Define a target using decorator syntax
# The decorated method may be named anything.
@builder.target(
    name='run',
    help='Run the project',
    needs=['build'],
)
def target_run(ctx: sbsf.TargetContext):
    print('Running...')

# Pass control to sbsf's default main implementation.
if __name__ == '__main__':
    sys.exit(builder.cli_main())

    # Or, roll your own main:
    # builder.resolve_targets(['build', run'])
```

After creating a `sbsf` script, you may then invoke it as you would any other Python script. Each argument corresponds to one target to resolve. For example, the following command will resolve the `build` and `run` targets (in that order), defined in a file named `builder.py`.

```bash
python3 builder.py build run
```

Note that in the above example, the `run` target declared `build` as a dependency (see the `needs=` parameter). Therefore, specifying `build` and `run` at the same time is redundant. You can specify just `run` which will implicitly resolve `build` first.


### GNU Make-like behavior

`sbsf` targets are roughly analogous to GNU Make's [phony targets](https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html).

In other words, `sbsf` does not tie a target to a file on the filesystem. Targets are always resolved regardless of the state of the filesystem.

To emulate GNU Make's behavior, `sbsf` provides a utility method `check_stale`. It accepts a list of 'input' files, and a list of 'output' files. It returns true if any input file is newer than any output file (by checking each file's mtime). If using `sbsf`'s default main implementation, it also returns true if the `--always-make` flag is set.

An example of `check_stale` in practice is provided below.

```py
@builder.target(
    name='hello.txt',
    help='Generate hello.txt',
)
def target_hello(ctx: sbsf.TargetContext):
    if not ctx.check_stale([], ['hello.txt']):
        return
    with open('hello.txt', 'w') as out_file:
        out_file.write('Hello, world\n')

@builder.target(
    name='intro.txt',
    help='Generate intro.txt',
    needs=['hello.txt'],
)
def target_intro(ctx: sbsf.TargetContext):
    if not ctx.check_stale(['hello.txt'], ['intro.txt']):
        return
    with open('intro.txt', 'w') as out_file:
        with open('hello.txt', 'r') as in_file:
            out_file.write(in_file.read())
        out_file.write('My name is sbsf\n')
```


## Testing

To run the unit tests, use this command:

```bash
python3 builder.py test
```

To run a more involved test against an existing example project, use this command:

```bash
python3 builder.py examples
```

