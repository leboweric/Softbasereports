# Contributing to Forklift Reporting System

Thank you for your interest in contributing to the Forklift Reporting System! This document provides guidelines for contributing to this project.

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd forklift-reporting-system
   ```

2. **Backend Setup**
   ```bash
   cd reporting-backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd reporting-frontend
   npm install
   ```

4. **Environment Configuration**
   - Copy `.env.example` to `.env` in both frontend and backend directories
   - Configure your API keys and database settings

## Development Workflow

### Running the Application

1. **Start the Backend**
   ```bash
   cd reporting-backend
   source venv/bin/activate
   python src/main.py
   ```

2. **Start the Frontend**
   ```bash
   cd reporting-frontend
   npm run dev
   ```

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Backend tests
   cd reporting-backend
   python -m pytest

   # Frontend tests
   cd reporting-frontend
   npm test
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and small

### JavaScript/React (Frontend)
- Use ES6+ features
- Follow React best practices
- Use functional components with hooks
- Keep components small and focused

### General
- Write clear, descriptive commit messages
- Add comments for complex logic
- Update documentation for new features

## Pull Request Process

1. **Ensure your code follows the style guidelines**
2. **Add or update tests as needed**
3. **Update documentation**
4. **Create a pull request with:**
   - Clear description of changes
   - Screenshots for UI changes
   - Testing instructions

## Reporting Issues

When reporting issues, please include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, browser, versions)
- Screenshots or error logs if applicable

## Feature Requests

For feature requests, please:
- Check if the feature already exists or is planned
- Provide a clear use case
- Describe the expected behavior
- Consider the impact on existing functionality

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain a professional environment

## Questions?

If you have questions about contributing, please:
- Check the documentation first
- Search existing issues
- Create a new issue with the "question" label

Thank you for contributing to the Forklift Reporting System!

