# SimpleExtractor

SimpleExtractor is an extractor for .spmod mod files, used in Simple Planes

> SimpleRockets2 (aka Juno: New Origins) support is also planned

The code is based on reverse-engineered game .dll's from Simple Planes

## Usage

```
$ python main.py mod.spmod
```

Will extract assetBundles for platforms, included in the mod

## Possible issues

Since the unpacker is in its early version, it may have some issues, including, but not limited to:

- The unpacker may not be ready to unpack old mods
- The unpacker may not be able to unpack "bundled" mods

In case of getting an error, reach us out in issues, including mod you were trying to unpack
