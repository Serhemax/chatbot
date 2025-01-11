# Chatbot
Chatbot for work with documents

## Prerequisites
- Install Ollama - https://ollama.com/
- Install Python 3

## Download Llama 3 model 
In your terminal:

  `ollama pull llama3:8b`

## Create Python Virtual Env
Via conda (miniconda):

```
  conda create --name local-llm python=3.12
  conda activate local-llm
```

Or via Python Venv:

```
  python -m venv env​
  source env/bin/activate​
```
​
To deactivate env after the session run:
  
  `deactivate​`

## Install Python libraries
In your terminal:

  `pip install -r requirements.txt`

## Run the Flask app

  `flask run`
