# Development Guide

## 🛠️ Development Workflow

### **Local Development (Manual)**

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install/update dependencies
pip install -r requirements.txt

# 3. Run the application from project root
cd src
python app/main.py
```

### **Alternative: Run as module**
```bash
# From project root
export PYTHONPATH="src:$PYTHONPATH"
python -m app.main
```

### **Docker Development**

```bash
# Build and run container
docker build -t icp-identity .
docker run -p 8099:8099 -v $(pwd)/data:/data icp-identity

# Or with docker-compose
docker-compose up icp-identity
```

## 🧪 Testing Endpoints

The application will be available at:
- **Local:** `http://localhost:8099`
- **Docker:** `http://localhost:8099`

### **Key Endpoints:**

**General:**
- `GET /` - Web dashboard
- `GET /identity` - Identity information
- `GET /health` - Health check
- `GET /stats` - Application statistics
- `GET /status` - Application status

**Canister Management:**
- `GET /canisters/list` - List all registered canisters
- `POST /canisters/add` - Add a new canister to registry
- `DELETE /canisters/{canister_id}` - Remove canister from registry
- `GET /canisters/{canister_id}` - Get canister information

**Dynamic Canister Methods (auto-generated from .did files):**
- `POST /canisters/{canister_id}/login` - Login to canister
- `POST /canisters/{canister_id}/register` - Register with canister
- `GET /canisters/{canister_id}/getConversations` - Query conversations
- `POST|GET /canisters/{canister_id}/{method_name}` - Any method from .did file

**Identity Management:**
- `POST /regenerate` - Regenerate identity
- `GET /backups` - List identity backups
- `POST /backup` - Create identity backup

## 🎯 Complete Workflow

### **Automatic Startup Process:**
1. **Identity Creation** - Addon automatically creates LocalICIdentity on startup
2. **Environment Setup** - Configures IC network settings (mainnet/testnet/local)
3. **Web Dashboard** - Launches at `http://localhost:8099` with canister management UI

### **Adding Canisters via UI:**
1. **Open Dashboard** - Navigate to `http://localhost:8099`
2. **Add Canister** - Use the "Add New Canister" form
3. **Auto-Authentication** - Addon automatically authenticates with the canister
4. **Method Discovery** - Parses `.did` file to show available methods as buttons

### **API Workflow Example:**

```bash
# 1. Add a canister (auto-authenticates)
POST /canisters/add
{
  "canister_id": "3y3bg-2qaaa-aaaaj-azroa-cai",
  "name": "M_AUTONOME",
  "network": "mainnet"
}

# 2. List available canisters
GET /canisters/list

# 3. Call canister methods directly
POST /canisters/3y3bg-2qaaa-aaaaj-azroa-cai/login
{}

POST /canisters/3y3bg-2qaaa-aaaaj-azroa-cai/register
{
  "args": ["username", "fullname", "bio", "avatar"]
}

# 4. Query methods (read-only)
GET /canisters/3y3bg-2qaaa-aaaaj-azroa-cai/getConversations
```

## 📁 Project Structure

```
src/
├── app/                     # Application entry point
│   └── main.py             # Start here for development
├── core/                   # Core infrastructure
├── identity/               # Identity management
├── controllers/            # Canister controllers
├── integrations/          # External integrations
├── utils/                 # Utilities
└── data/                  # Static data & interfaces
```

## 🔧 Development Tips

1. **Always run from `src/` directory** for proper imports
2. **Use Postman** to test API endpoints
3. **Check logs** for debugging information
4. **Environment variables** are set via addon configuration or options.json