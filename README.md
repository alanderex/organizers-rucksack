# Pretalx Conference Suite

Provide a simple interface to pretalx for:
- submissions
- speaker
- reviews
- handling of custom questions

While keeping private data private.

Pull and mangle data from pretalx to interact with other services.

The API provides an interface to all [pretalx endpoints as described here](https://docs.pretalx.org/api/resources/index.html).

## Use cases

* Share a json to generate a website with sessions
* Get speaker info to send tickets automatically via another platform 
* Get stats on submissions, reviews
* Get prepared data to explore via JupyterLab

## Benefits

A domain driven interface for getting data from pretalx.


## Usage

### 1. Create a New Project

Create a project directory in `/projects` or copy `/projects/template-project`,  mae it e.g. `/projects/my-conference`

### 2. Configure Project = Conference

Open `/projects/my-conference/config.yml` and edit it.

The slug can be found in pretalx: Settings/General/, field 'Short form'. It will look like 'https://pretalx.com/my-conference-slug'. 
The slug is the last part of the URL only, i.e. 'my-conference-slug'

For further use you can also set your conference name and email for the program team, currently this is not used, yet.

```yaml
# Project name, same as directory
name: my-conference

# Event slug in pretalx
pretalx_event_slug: my-conference-slug

# Conference Settings
conference_name: "EuroPython 2022"
program_addy: program-wg@europython.eu
```

### 3. Understanding how Configuration works

The main configuration file is located at `app/config/config.yml`. This file contains the basic configuration should not be altered.

Any configuration provided in `/projects/my-conference/config.yml` will supersede configs in `app/config/config.yml`, for example:

```yaml
# app/config/config.yml
# Project name, same as directory
name: unset-conference-name
```

```yaml
# /projects/my-conference/config.yml
# Project name, same as directory
name: my-conference
```

#### Accessing Configuration

This project utilizes [OmegaConf](https://omegaconf.readthedocs.io/en/2.1_branch/) to read and manage configuration.

OmegaConf provides a dictionary with dot-notation and can be accessed via `CONF` 

```python


```


---

## Set-Up Python Project

Clone the repository and `cd` into `pyconference-pretalx`.

```shell
git clone # TODO add once published
cd pyconference-pretalx
````

##### Environment

###### conda
```shell
conda env create -f environment.yml
```
Make sure you have selected the `gtools` environment in your IDE when you run test or in the shell

```shell
conda activate pyconference-pretalx
```


--- 
## Set-Up: Pretalx token

put here: TODO

Config stuff: TODO
--- 
## Set-Up: DropBox

- sync file from directory to local directory
- read only implemented

Make sure to create app in:  
[https://www.dropbox.com/developers/apps](https://www.dropbox.com/developers/apps)  
The access token is short-lived! but it can be re-generated.   
For persistent sign in use Oauth2

* token auth: save token as text file with just the token and add the filename in config.yml: dropbox.token_file_name
* for OAuth: save yaml in dropbox.credentials_file_name:
```yaml
app_key: APP-KEY-HERE
app_secret: SECRET-KEY-HERE
```


### Project

The project manages to which services access is granted.  

Create a project with a descriptive name and identifier.

