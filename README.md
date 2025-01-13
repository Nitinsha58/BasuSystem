# Basu System

A Django-based management system for educational institutions.

## Setup

1. Clone the repository:
    ```
    git clone git@github.com:Nitinsha58/BasuSystem.git
    cd BasuSystem
    ```
2. Create a virtual environment and install dependencies:
    ```
    python -m venv env source env/bin/activate 
    # For Windows: env\Scripts\activate pip install -r requirements.txt
    ```
3. Add Dependencies
    ```
    pip install -r requirements.txt
    ```

4. Create a `.env` file:
    ```
    DJANGO_SETTINGS_MODULE=config.django.local 
    SECRET_KEY=your-secret-key 
    DJANGO_DEBUG=True
    ```

5. Run migrations:

    ```
    python manage.py migrate
    ```
6. Start the development server:
    ```
    python manage.py runserver
    ```


## Contributing
- Fork the repo and create a feature branch for your changes.
- Open a pull request with a clear description of your feature.


