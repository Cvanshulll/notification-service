
# Notification Service

This project is a backend service to send notifications to users using different channels like Email, SMS, and Push.  
It is designed to handle notifications asynchronously and scale easily.

---

## Project Overview

The system allows users to:
- Send notifications
- Track their status
- Manage notification preferences

It uses a queue system so that notifications are processed in the background instead of blocking the API.

---

## Tech Stack (with reason)

- Django + Django REST Framework → easy and fast API development  
- PostgreSQL → reliable relational database  
- Redis → used as message broker  
- Celery → handles background tasks (async processing)  
- Docker → makes setup easy and consistent across environments  

---

## Setup Instructions (Local)

### 1. Clone the repository
```
git clone <repo-url>
cd notification-service
```
---

### 2. Start services using Docker
```
docker-compose up --build
```
---

### 3. Run database migrations

```
docker-compose exec web python manage.py migrate
```

---


## API Testing

APIs were tested using Postman.

Base URL:
```
http://localhost:8000/api/
```

---

## API Endpoints

- POST `/notifications/` → Send notification  
- GET `/notifications/:id/` → Get notification status  
- GET `/notifications/user/:userId/` → Get user notification history  
- POST `/preferences/` → Set user preferences  
- GET `/preferences/:userId/` → Get user preferences  

---

## Example Requests

### Send Notification

```
POST /api/notifications/
````

```json
{
  "user_id": "user123",
  "channel": "email",
  "priority": "high",
  "message": "Your order has been shipped!"
}
````

---

### Send Notification using Template

```json
{
  "user_id": "user123",
  "channel": "email",
  "template_name": "order_shipped",
  "template_vars": {
    "name": "John",
    "order_id": "ORD-12345"
  }
}
```

---

## Running Tests

```
python manage.py test
```

---

## Postman Collection

Postman collection is included in the repository for testing APIs.

---

## Assumptions

* Authentication is not implemented (can be added later)
* User data is assumed to exist
* Notification providers are mocked (no real email/SMS integration)
* Templates are stored in memory
