# q

One man production management.

## Installing

Get the copy
```bash
git clone https://github.com/wigy/q.git
```
and link the binary to somewhere along your `$PATH`:
```bash
cd q
sudo ln -s bin/q /usr/local/bin
```

Now get to your project folder (or any folder above it) and type
```bash
q settings save
```

You need to tune settings in `.q` according to your project.
At least you need to set project name and directory to store ticket meta data.
```
APP=MyProject
WORKDIR=/home/me/tickets
```

For further help, you can use
```bash
q help
```

## Configuring

TODO: List all variables and their possible values here.