# System Design Document

---

## High-Level Architecture

Client → Django API → PostgreSQL  
                     ↓  
                 Redis Queue  
                     ↓  
             Celery Worker → Providers  

---

## Database Schema

### Notification Table

Stores all notifications.

Fields:
- user_id → identifies user  
- channel → email/sms/push  
- status → pending/sent/failed  
- message → actual content  
- retry_count → retry tracking  
- created_at → timestamp  

---

### UserPreference Table

Stores user settings.

Fields:
- user_id → unique user  
- email_enabled → true/false  
- sms_enabled → true/false  
- push_enabled → true/false  

---

## Failure Handling

- If sending fails → retry using Celery  
- Max retries → 3  
- Delay increases (2s, 4s, 8s)  

### Cases:
- Timeout → retry  
- Invalid data → mark failed  
- Duplicate request → ignore (idempotency)  

---

## Scalability

Current:
- Single API + worker  
- Works fine for small load  

To scale:
- Add more Celery workers  
- Use Redis cluster  
- Add DB replicas  
- Use load balancer  

---

## Trade-offs

- Mock providers → easier to implement  
- In-memory templates → simple but not scalable  
- Single Redis → easy setup but not fault-tolerant  