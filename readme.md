# Batch Parelle AI Serving

This repo is to Replicate Ollama serving by our own understanding.


<img src="./overall.png">

**maybe all of them are wrong at all**

it is just the project for our course while we are fxcked by our professor to tell us do a lot of projects at the same period.
  - i.e. We don't have the fxcking time to research it.

- python backend 
  - asycio
  - unicorn
  
- lallma inference script:
  - TODO

A test reqeust:
- Windows Powershell:
  ```
  curl -Uri "http://127.0.0.1:8000/inference" -Method POST -Body '{"request": 42}' -ContentType "application/json"
  ```