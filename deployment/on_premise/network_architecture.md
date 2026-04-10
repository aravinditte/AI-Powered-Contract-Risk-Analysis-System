# Network Architecture

## Overview

[User Browser]
      |
      v
[Internal Load Balancer]
      |
      v
[Frontend (Nginx)]
      |
      v
[Backend API (FastAPI)]
      |
      v
[PostgreSQL Database]

## Security Principles
- No public internet exposure
- Backend accessible only from frontend
- Database isolated in private subnet
- Audit logs retained internally
