# Home Assistant ICP Identity Manager Addon

Give your Home Assistant instance a unique Internet Computer Protocol (ICP) identity for blockchain integration.

## Installation

### Option 1: Home Assistant Add-on Store (Recommended)

1. In Home Assistant, go to **Supervisor** → **Add-on Store**
2. Click the menu (⋮) in the top right corner
3. Select **Repositories**
4. Add this repository URL: `https://github.com/your-username/home_assistant_identity`
5. Click **Add**
6. Find "ICP Identity Manager" in the add-on store
7. Click **Install**

### Option 2: Manual Installation

1. Copy the entire addon folder to your Home Assistant addons directory:
   ```bash
   cp -r icp-identity-addon /usr/share/hassio/addons/local/
   ```

2. Restart Home Assistant Supervisor
3. The addon will appear in your local add-ons list

## Configuration

### Addon Options

Configure the addon through the Home Assistant interface:

```yaml
network: "local"                 # Network type: local, testnet, mainnet
generate_new_identity: false     # Force generation of new identity
canister_endpoints: []           # List of canister IDs to interact with
```

### Configuration Examples

**Basic Setup:**
```yaml
network: "mainnet"
generate_new_identity: false
canister_endpoints: []
```

**Development Setup:**
```yaml
network: "local"
generate_new_identity: true
canister_endpoints: 
  - "rdmx6-jaaaa-aaaaa-aaadq-cai"
```

## Usage

### Starting the Addon

1. Install and configure the addon
2. Click **Start**
3. Check the logs for your generated principal ID
4. Access the web interface at `http://homeassistant.local:8099`

### Home Assistant Sensors

The addon automatically creates these sensors:

- **`sensor.icp_principal`**: Your ICP Principal ID
- **`sensor.icp_connection`**: ICP network connection status

Use these sensors in your automations:

```yaml
automation:
  - alias: "ICP Identity Status"
    trigger:
      platform: state
      entity_id: sensor.icp_connection
    action:
      service: notify.notify
      data:
        message: "ICP connection status: {{ trigger.to_state.state }}"
```

### Web Interface Features

Access the web dashboard at `http://homeassistant.local:8099` to:

- View your ICP Principal ID and public key
- Create manual backups
- Regenerate identity (with automatic backup)
- Monitor storage statistics
- View backup history

### API Endpoints

The addon provides RESTful API endpoints:

- **GET** `/identity` - Get identity information
- **POST** `/regenerate` - Regenerate identity
- **GET** `/backups` - List all backups
- **POST** `/backup` - Create new backup
- **GET** `/stats` - Get storage statistics

Example API usage:
```bash
curl http://homeassistant.local:8099/identity
```

## Security

### Identity Storage

- **Mnemonic phrases** are encrypted using NaCl SecretBox
- **Private keys** never leave the addon container
- **Backups** include encrypted identity files
- **Encryption keys** are randomly generated per identity

## Development

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/home_assistant_identity.git
   cd home_assistant_identity
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run locally:
   ```bash
   cd src
   python main.py
   ```

### File Structure

```
icp-identity-addon/
├── config.yaml              # Addon configuration
├── Dockerfile               # Container definition  
├── run.sh                   # Startup script
├── requirements.txt         # Python dependencies
├── src/
│   ├── main.py             # Main addon logic
│   ├── icp_identity.py     # ICP identity management
│   ├── ha_integration.py   # Home Assistant integration
│   └── storage.py          # Identity storage & backups
└── README.md               # This file
```

## Troubleshooting

### Common Issues

**Addon won't start:**
- Check Home Assistant logs: `docker logs hassio_supervisor`
- Verify addon configuration is valid YAML
- Ensure all required options are set

**Identity generation fails:**
- Check available disk space in `/data`
- Verify Python dependencies are installed
- Review addon logs for specific error messages

**Web interface not accessible:**
- Confirm port 8099 is not blocked by firewall
- Check if addon is running: Supervisor → ICP Identity Manager
- Verify network configuration in addon options

**Home Assistant sensors not appearing:**
- Check if `SUPERVISOR_TOKEN` environment variable is available
- Verify Home Assistant API is accessible
- Review addon logs for sensor creation errors

### Log Access

View addon logs in Home Assistant:
1. Go to **Supervisor** → **ICP Identity Manager**
2. Click **Logs** tab
3. Check for errors or status messages
