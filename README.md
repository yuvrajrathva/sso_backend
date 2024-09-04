## Installation Guide (Backend)

- Activate the virtual environment

    ```
     pipenv shell
     ```

- Install the required packages

    ``` 
    pipenv install
    ```

- Run the following command to start the server

    ``` 
    uvicorn app.main:app --host localhost --port 8000 --reload
     ```
 

