# wine_wrap

A versioned wine-prefix management tool with memory-shared prefixes.

This tool simplifies the maintenance of individual wine-prefixes per executable.
Each prefix is version-controlled using git, allowing for reproducible setups.
Furthermore (if supported by host system), the prefixes are stored as subvolumes on a BTRFS image. This makes storing them more memory efficient by only saving differences between each installation.

## Installation

`wine_wrap` can be installed using `pip`:

```bash
$ pip install wine_wrap
```

## Usage

```bash
$ wine_wrap --help
Usage: wine_wrap [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  clear      Clear all associations.
  configure  Associate script with given wine-prefix.
  run        Execute given script in wine-prefix.
  scan       Scan for executables in given prefix.
  set        Associate script with given wine-prefix.
  show       Show current setup.
```

## Getting started

A typical use-case would be to first run an installer, and then the created executable in the same wine-prefix.
To do so, first run the installer (as well as winecfg beforehand) and name the used prefix:

```bash
$ wine_wrap run --configure --name MyOwnPrefix installer.exe
[..]
```

Afterwards, find the newly installed executable within this prefix and associate it correctly:

```bash
$ wine_wrap scan MyOwnPrefix
[..]
 > "/path/to/executable.exe"
[..]
$ wine_wrap set "/path/to/executable.exe" MyOwnPrefix
```

We can then make sure that the correct script-prefix associations are set:

```bash
$ wine_wrap show
--- MyOwnPrefix ---
 > installer.exe
 > executable.exe
```

It is then possible to simply run the executable in the correct wine-prefix:

```bash
$ wine_wrap run /path/to/executable.exe
[..]
```

If we don't need the scripts anymore, we can delete them in the end:

```bash
$ wine_wrap clear --delete-prefixes --prefix MyOwnPrefix
[..]
```
