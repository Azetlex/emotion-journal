# Emotion Journal

A web application developed as a bachelor's thesis project, designed to help users record their emotions, organize personal journal entries, and visualize emotional patterns through statistics.

## Features

- User registration and authentication
- Personal journal entries
- Organization of entries by topics
- Emotion tracking
- Statistical visualizations
- Editing and deleting journal entries

## Technologies

- **Backend:** Python, Django 4.2
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Data visualization:** Matplotlib

## Getting Started

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd YOUR_REPOSITORY_NAME
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```cmd
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure the application

Set the `DJANGO_SECRET_KEY` environment variable for your local environment.

### 5. Initialize the database

```bash
python manage.py migrate
```

### 6. Run the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## Project Status

This project is being updated and prepared for public portfolio use. Security improvements, automated tests, and deployment configuration are in progress.

## Background

Originally developed as a bachelor's thesis, this project combines web development with emotion tracking and personal reflection.