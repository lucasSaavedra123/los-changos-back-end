# Walletify Django-based Back-End Development

<p align="center">
  <img src="https://user-images.githubusercontent.com/46687572/190235826-52677e5c-736b-4d72-bf09-2c43bd10ed40.png" />
</p>

![Workflow Status](https://github.com/lucasSaavedra123/los-changos-back-end/actions/workflows/django.yml/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/lucasSaavedra123/los-changos-back-end/badge.svg?branch=master)](https://coveralls.io/github/lucasSaavedra123/los-changos-back-end?branch=master)

Official Repository of Walletify. Website: [Link](www.walletify-backend.herokuapp.com/)

## Contribute

### Virtual Environment

We strongly recommend to use virtual environments to develop for the Walletify back-end. There are two straightforward ways to do this:

#### Conda
To install the enviroment from Conda just type:

    conda env create -n "walletify-env" python=3.9

Then, activate it:

    conda activate walletify-env

Finally, install the requirements:

    pip install -r requirements.txt

#### venv
Verify your python version (It should be 3.9 or greater):

    python --version
 
Create the environment:

    python -m venv walletify-env

Activate it:

    source walletify-env/bin/activate #Linux
    ./walletify-env/bin/activate.ps1 #PowerShell (Windows)

Finally, install the required modules:

    pip install -r requirements.txt

### Generate requirements.txt

    pip freeze > requirements.txt

**Start Coding!**
