# Home Assistant Identity Manager

A Python-based identity management system for Internet Computer (IC) canisters, designed to integrate with Home Assistant. This project provides a REST API for managing IC identities, canisters, and blockchain interactions.

## Quick Start

### Python Development Setup

1. **Create and activate virtual environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

   The API server will start on `http://localhost:8099`

### Docker Setup

1. **Build the Docker image**
   ```bash
   docker build -t home-assistant-identity .
   ```

2. **Run the container**

   **Detached mode (recommended for production):**
   ```bash
   docker run -d --name ic-identity-api -p 8099:8099 home-assistant-identity
   ```

   **Attached mode (for debugging):**
   ```bash
   docker run -it --rm -p 8099:8099 home-assistant-identity
   ```

3. **Test the API**
   ```bash
   curl http://localhost:8099/health
   curl http://localhost:8099/api/v1/identity
   ```

## Home Assistant Integration

This project is designed to integrate seamlessly with Home Assistant. For detailed integration instructions, see:

**[📖 Home Assistant Integration Guide](homeassistant_resources/README.md)**

The integration guide covers:
- Adding the service to Home Assistant
- Setting up the custom Lovelace card
- Configuring the dashboard
- Troubleshooting common issues

## 📁 Project Structure

### Core Application

- **`main.py`** - Application entry point and server startup
- **`requirements.txt`** - Python dependencies and versions

### API Layer

- **`api/`** - REST API implementation
  - **`api.py`** - Main API server setup and routing
  - **`controllers/`** - API endpoint controllers
    - **`canister_controller.py`** - Canister management endpoints
    - **`identity_controller.py`** - Identity management endpoints

### Identity Management

- **`identity/`** - Identity and cryptographic functionality
  - **`identity_manager.py`** - Main identity management class
  - **`ic_identity.py`** - IC identity implementation
  - **`ic_private_key.py`** - Private key management
  - **`ic_anonymous_identity.py`** - Anonymous identity support
  - **`mnemonic.py`** - BIP39 mnemonic phrase handling

### Actor Controller

- **`actor_controller/`** - IC canister interaction layer
  - **`actor.py`** - Canister actor implementation
  - **`agent.py`** - IC agent for network communication

### Data Storage

- **`data/`** - Persistent data storage
  - **`canisters/`** - Canister interface definitions (.did files)
  - **`identity/`** - Identity files and configurations

### Utilities

- **`utils/`** - Helper utilities and parsers
  - **`helpers/`** - Candid interface parsing utilities
    - **`candid_parser_helpers.py`** - Functions for parsing Candid interface files (comment stripping, balanced block parsing)
  - **`parsers/`** - Data parsing utilities
    - **`subacount_parsers.py`** - Subaccount data transformation

### Home Assistant Resources

- **`homeassistant_resources/`** - Home Assistant integration files
  - **`icp-addon-card.js`** - Custom Lovelace card for the UI
  - **`README.md`** - Detailed integration instructions

### Configuration

- **`Dockerfile`** - Docker container configuration

## API Endpoints

The application exposes the following REST endpoints:

- `GET /health` - Health check
- `GET /api/v1/identity` - Get current identity
- `POST /api/v1/identity/regenerate` - Regenerate identity
- `GET /api/v1/canisters` - List all canisters
- `POST /api/v1/canisters/add` - Add a new canister
- `POST /api/v1/canisters/call` - Call a canister method
- `DELETE /api/v1/canisters/delete/{name}` - Delete a canister

## 🧪 Testing

### Test the API

```bash
# Health check
curl http://localhost:8099/health

# Get identity
curl http://localhost:8099/api/v1/identity

# List canisters
curl http://localhost:8099/api/v1/canisters

# Add a canister
curl -X POST http://localhost:8099/api/v1/canisters/add \
  -H "Content-Type: application/json" \
  -d '{"canister_id": "your-canister-id", "canister_name": "my-canister"}'
```

### Docker Testing

```bash
# Build and test in one command
docker build -t home-assistant-identity . && \
docker run -d --name test-api -p 8099:8099 home-assistant-identity && \
sleep 5 && \
curl http://localhost:8099/health && \
docker stop test-api && docker rm test-api
```

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using port 8099
   lsof -i :8099
   # Or on Windows
   netstat -ano | findstr :8099
   ```

2. **Docker container won't start**
   ```bash
   # Check logs
   docker logs ic-identity-api
   
   # Run interactively for debugging
   docker run -it --rm -p 8099:8099 home-assistant-identity python main.py
   ```

3. **Dependencies not found**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

### Logs

The application logs to stdout/stderr. In Docker:
```bash
docker logs ic-identity-api -f
```
