# LungScanAI

A medical imaging application for lung scan analysis using AI/ML.

## Features

- Upload and analyze lung scan images
- AI-powered analysis of medical images
- Secure user authentication
- Responsive web interface

## Prerequisites

- Python 3.9+
- PostgreSQL
- pip
- Git

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/LungScanAI.git
   cd LungScanAI
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Update the variables in `.env` with your configuration

5. **Initialize the database**
   ```bash
   flask db upgrade
   ```

6. **Run the development server**
   ```bash
   flask run
   ```

## Deployment

### Render (Backend)

1. **Create a new Web Service**
   - Connect your GitHub repository
   - Select the repository and branch
   - Configure the following settings:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn --worker-tmp-dir /dev/shm --workers 2 --threads 4 --worker-class gthread --timeout 120 --bind 0.0.0.0:$PORT app:app`

2. **Set environment variables**
   - Add all variables from `.env.example` to Render's environment variables

3. **Deploy**
   - Click "Deploy" to start the deployment process

### Vercel (Frontend)

1. **Import your project**
   - Connect your GitHub repository
   - Select the repository and branch

2. **Configure the project**
   - **Framework Preset**: Next.js
   - **Build Command**: `npm run build` or `yarn build`
   - **Output Directory**: `out` or `.next`
   - **Install Command**: `npm install` or `yarn`

3. **Set environment variables**
   - Add `NEXT_PUBLIC_API_URL` with your Render backend URL

4. **Deploy**
   - Click "Deploy" to start the deployment process

## Environment Variables

See `.env.example` for a list of required environment variables.

## Project Structure

```
LungScanAI/
├── app/                      # Application package
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── routes/              # Route handlers
│   ├── static/              # Static files (CSS, JS, images)
│   └── templates/           # HTML templates
├── migrations/              # Database migrations
├── tests/                   # Test files
├── .env.example             # Example environment variables
├── .gitignore
├── config.py                # Configuration settings
├── requirements.txt         # Dependencies
├── runtime.txt              # Python version for Render
├── wsgi.py                  # WSGI entry point
└── README.md
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
