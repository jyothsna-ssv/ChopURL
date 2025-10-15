# ChopURL - Modern URL Shortening Service

A full-stack URL shortening service built with FastAPI backend and Vue.js frontend, featuring custom short codes, analytics, and a beautiful admin interface.

![ChopURL Logo](admin/public/favicon.png)

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

### ✨ **Core Functionality**
- **🔗 URL Shortening** - Create short, memorable links instantly
- **🎯 Custom Short Codes** - Use your own custom short codes
- **📊 Click Analytics** - Track clicks and engagement metrics
- **⚡ Instant Redirects** - Lightning-fast URL redirection with Redis
- **🔧 Link Management** - View, delete, and manage all your links

### 🎨 **User Interface**
- **📱 Responsive Design** - Works perfectly on all devices
- **🎨 Modern UI/UX** - Beautiful, professional interface
- **📈 Real-time Stats** - Live analytics dashboard
- **🗂️ Pagination** - Efficient browsing with 8 links per page
- **🔍 Search & Filter** - Easy link management

### 🚀 **Performance**
- **⚡ Sub-millisecond redirects** with Redis backend
- **📊 Real-time analytics** and click tracking
- **🔄 Auto-generated short codes** with collision detection
- **🛡️ Duplicate code validation** with user-friendly error messages

---

## Tech Stack

### **Backend**
- **FastAPI** - Modern, fast web framework for building APIs
- **Redis** - In-memory data store for ultra-fast redirects
- **Python 3.11+** - High-performance backend language
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server for running the application

### **Frontend**
- **Vue 3** - Progressive JavaScript framework
- **Vite** - Lightning-fast build tool and dev server
- **Vue Router** - Client-side routing
- **Axios** - HTTP client for API communication
- **Modern CSS** - Responsive design with gradients and animations

### **Infrastructure**
- **Redis** - In-memory database for caching and sessions
- **CORS** - Cross-origin resource sharing
- **Environment Variables** - Secure configuration management

---

## Project Structure

```
chopurl/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── api/
│   │   │   └── routers.py     # API route definitions
│   │   ├── core/
│   │   │   └── config.py      # Application configuration
│   │   ├── db/
│   │   │   └── redis_client.py # Redis database connection
│   │   ├── models/
│   │   │   └── schemas.py      # Pydantic data models
│   │   ├── services/
│   │   │   └── links.py        # Business logic for URL operations
│   │   └── utils/
│   │       └── hashids.py      # URL encoding utilities
│   └── requirements.txt        # Python dependencies
├── admin/                       # Vue.js frontend
│   ├── src/
│   │   ├── components/         # Vue components
│   │   │   ├── ShortenForm.vue    # URL shortening form
│   │   │   ├── LinksTable.vue     # Links management table
│   │   │   └── StatsModal.vue     # Analytics modal
│   │   ├── views/              # Page components
│   │   │   ├── Home.vue           # Landing page
│   │   │   └── Links.vue          # Links dashboard
│   │   ├── router/              # Vue Router configuration
│   │   ├── api.ts               # Axios API client
│   │   └── main.js              # Application entry point
│   ├── public/
│   │   └── favicon.png          # Custom favicon
│   └── package.json             # Node.js dependencies
├── .env                        # Environment variables
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
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

#### **Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
```

#### **Windows:**
Download and install Redis from the official website or use Docker:
```bash
docker run -d -p 6379:6379 redis:7-alpine
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
source venv/bin/activate  # On Windows: venv\Scripts\activate
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

2. **Frontend Access:**
   Open `http://localhost:5173` in your browser

3. **API Documentation:**
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

2. **Shorten URL:**
   - Method: `POST`
   - URL: `http://localhost:8000/api/v1/shorten`
   - Body: `{"url": "https://www.google.com"}`

3. **Test Redirect:**
   - Method: `GET`
   - URL: `http://localhost:8000/{short_code}`

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

## Features Implementation Details

### **🔗 URL Shortening**
- **Auto-generated codes:** 6-character alphanumeric codes
- **Custom codes:** User-defined short codes with validation
- **Collision detection:** Prevents duplicate custom codes
- **URL validation:** Ensures valid URLs before shortening

### **📊 Analytics System**
- **Click tracking:** Increments counter on each redirect
- **Real-time stats:** Live analytics dashboard
- **Performance metrics:** Total links, clicks, and averages
- **Historical data:** Creation timestamps and click history

### **🎨 User Interface**
- **Responsive design:** Mobile-first approach
- **Modern styling:** Gradients, shadows, and animations
- **Intuitive navigation:** Clear user flow and navigation
- **Error handling:** User-friendly error messages

### **⚡ Performance Optimizations**
- **Redis caching:** Sub-millisecond redirects
- **Efficient pagination:** 8 links per page for optimal performance
- **Lazy loading:** Components loaded on demand
- **Optimized builds:** Minified and compressed assets

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

## Acknowledgments

- **FastAPI** - For the amazing Python web framework
- **Vue.js** - For the progressive JavaScript framework
- **Redis** - For the lightning-fast in-memory database
- **Vite** - For the incredibly fast build tool

---

**Built with ❤️ by the ChopURL team**

---

*Last updated: January 2024*