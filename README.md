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
 


 
## Database Migrations

- Run the following command to create a new migration

    ``` 
    alembic revision --autogenerate -m "migration message"
    ```

- Run the following command to apply the migration

    ```
    alembic upgrade head
    ```


