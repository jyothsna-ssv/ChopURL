# ChopURL - Modern URL Shortening Service

A full-stack URL shortening service built with FastAPI backend and Vue.js frontend, featuring custom short codes, analytics, and a beautiful admin interface.

 <p align="center">
  <img src="admin/public/favicon.png" alt="FlowStory App Banner" width="250" height ="450" />
 </p>

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Prerequisites](#prerequisites)
5. [Local Development Setup](#local-development-setup)
6. [API Documentation](#api-documentation)
7. [Testing](#testing)
8. [Contributing](#contributing)
9. [License](#license)

---

## Features

## Core Functionality

- **Custom Short Links**  
  Create your own custom short codes for memorable URLs. Choose any short code you want for your links.

- **Click Tracking**  
  Monitor click counts for each shortened link. View detailed statistics and track link performance.

- **Instant Redirects**  
  Fast URL redirection with a Redis backend for lightning-quick access.

- **Link Management**  
  View all your shortened links in one dashboard. Delete individual links or clear all links at once.


---

## Tech Stack

### **Backend**
- **FastAPI** - Modern, fast web framework for building APIs
- **Redis** - In-memory data store for ultra-fast redirects
- **Python 3.11+** - High-performance backend language
- **Pydantic** - Data validation and settings management

### **Frontend**
- **Vue 3** - Progressive JavaScript framework
- **Vite** - Lightning-fast build tool and dev server
- **Vue Router** - Client-side routing
- **Axios** - HTTP client for API communication

### **Infrastructure**
- **Redis** - In-memory database for caching and sessions
- **CORS** - Cross-origin resource sharing
- **Environment Variables** - Secure configuration management

---

## Project Structure

```
chopurl/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── routers.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── db/
│   │   │   └── redis_client.py
│   │   ├── models/
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   └── links.py
│   │   └── utils/
│   │       └── hashids.py
│   └── requirements.txt
├── admin/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ShortenForm.vue
│   │   │   ├── LinksTable.vue
│   │   │   └── StatsModal.vue
│   │   ├── views/
│   │   │   ├── Home.vue
│   │   │   └── Links.vue
│   │   ├── router/
│   │   ├── api.ts
│   │   └── main.js
│   ├── public/
│   │   └── favicon.png
│   └── package.json
├── .env
├── .gitignore
└── README.md

```

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **Redis Server** - [Install Redis](https://redis.io/download)
- **Git** - [Download Git](https://git-scm.com/downloads)

### **Redis Installation**

#### **macOS (using Homebrew):**
```bash
brew install redis
brew services start redis
```

---

## Local Development Setup

### **1. Clone the Repository**
```bash
git clone <your-repo-url>
cd ChopURL
```

### **2. Backend Setup**

#### **Create Virtual Environment:**
```bash
python -m venv venv
source venv/bin/activate  
```

#### **Install Dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

#### **Start Redis Server:**
```bash
# Make sure Redis is running on port 6379
redis-cli ping  # Should return "PONG"
```

#### **Run Backend Server:**
```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend will be available at:** `http://localhost:8000`

### **3. Frontend Setup**

#### **Install Dependencies:**
```bash
cd admin
npm install
```

#### **Start Development Server:**
```bash
npm run dev
```

**Frontend will be available at:** `http://localhost:5173` (or next available port)

### **4. Verify Installation**

1. **Backend Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```
   Expected: `{"status":"healthy"}`
    

3. **Frontend Access:**
   Open `http://localhost:5173` in your browser

4. **API Documentation:**
   Visit `http://localhost:8000/docs` for interactive API docs

---

## API Documentation

### **Base URL:** `http://localhost:8000`

### **Endpoints**

#### **1. Health Check**
```http
GET /health
```
**Response:** `{"status":"healthy"}`


#### **2. Shorten URL**
```http
POST /api/v1/shorten
Content-Type: application/json

{
  "url": "https://www.example.com",
  "custom_code": "example"  // Optional
}
```

**Response:**
```json
{
  "short_code": "abc123",
  "original_url": "https://www.example.com",
  "short_url": "http://localhost:8000/abc123",
  "clicks": 0,
  "created_at": "2024-01-15T10:30:00"
}
```

#### **3. Redirect (Short URL)**
```http
GET /{short_code}
```
**Response:** HTTP 302 redirect to original URL

#### **4. Get Link Statistics**
```http
GET /api/v1/stats/{short_code}
```

**Response:**
```json
{
  "short_code": "abc123",
  "original_url": "https://www.example.com",
  "clicks": 5,
  "created_at": "2024-01-15T10:30:00"
}
```

#### **5. Admin - Get All Links**
```http
GET /api/v1/admin/links?skip=0&limit=10
```

#### **6. Admin - Delete Link**
```http
DELETE /api/v1/admin/links/{short_code}
```

#### **7. Admin - Clear All Links**
```http
DELETE /api/v1/admin/links/clear/all
```

---

## Testing

### **Manual Testing**

#### **1. Frontend Testing**
1. Open `http://localhost:5173`
2. **Test URL Shortening:**
   - Enter a long URL
   - Click "Shorten URL"
   - Verify short URL is generated
3. **Test Custom Codes:**
   - Enter a custom code
   - Verify it works
   - Try duplicate custom code (should show error)
4. **Test Analytics:**
   - Click on generated links
   - View stats in dashboard
5. **Test Management:**
   - Navigate to "View All Links"
   - Test pagination (8 links per page)
   - Test delete functionality
   - Test "Clear All" functionality

#### **2. API Testing with Postman**

**Create Postman Collection:**

1. **Health Check:**
   - Method: `GET`
   - URL: `http://localhost:8000/health`
<p align="center">
  <img src="admin/public/p1.png" alt="Backend Health Check" width="250" height ="450" />
 </p>

2. **Shorten URL:**
   - Method: `POST`
   - URL: `http://localhost:8000/api/v1/shorten`
   - Body: `{"url": "https://www.google.com"}`
<p align="center">
  <img src="admin/public/p2.png" alt="Backend Health Check" width="250" height ="450" />
 </p>
3. **Test Redirect:**
   - Method: `GET`
   - URL: `http://localhost:8000/{short_code}`
<p align="center">
  <img src="admin/public/p3.png" alt="Backend Health Check" width="250" height ="450" />
 </p>
4. **Get Stats:**
   - Method: `GET`
   - URL: `http://localhost:8000/api/v1/stats/{short_code}`

5. **Admin Operations:**
   - Method: `GET`
   - URL: `http://localhost:8000/api/v1/admin/links`

### **Automated Testing**

#### **Backend API Tests:**
```bash
cd backend
python -m pytest tests/ -v
```

#### **Frontend Tests:**
```bash
cd admin
npm run test
```

---

## Local Development

The application is fully functional when running locally:

- **Frontend:** `http://localhost:5173` (or next available port)
- **Backend:** `http://localhost:8000`
- **API Docs:** `http://localhost:8000/docs`

---


## Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Add tests for new functionality**
5. **Commit your changes:**
   ```bash
   git commit -m "Add amazing feature"
   ```
6. **Push to the branch:**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### **Development Guidelines**
- Follow PEP 8 for Python code
- Use ESLint for JavaScript/Vue code
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

If you encounter any issues or have questions:

1. **Check the documentation** above
2. **Search existing issues** on GitHub
3. **Create a new issue** with detailed information
4. **Contact the maintainers**

---



---

**Built with ❤️ by the Jyothsna**

---
