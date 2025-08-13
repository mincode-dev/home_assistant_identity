# Home Assistant Integration Files

This directory contains all the configuration files needed to integrate the ICP Identity Addon with Home Assistant.

## 📁 File Overview

| File | Purpose | Usage |
|------|---------|-------|
| `working_configuration.yaml` | **WORKING CONFIG** | Complete tested Home Assistant configuration |
| `working_docker-compose.yml` | **WORKING SETUP** | Tested Docker Compose with both HA and ICP addon |
| `example_automation_test.yaml` | **TESTED AUTOMATIONS** | Working automation examples (boolean conditions fixed) |
| `empty_files.yaml` | **SETUP NOTES** | Notes about required empty files for HA |
| `icp_rest_sensor.yaml` | REST sensor configuration | Pulls real-time data from ICP addon |
| `icp_template_sensor.yaml` | Main template sensor | User-facing sensor for automations |
| `icp_sensors_package.yaml` | Package-based setup | Alternative setup using HA packages |
| `icp_sensors_template.yaml` | Standalone template | Direct template inclusion |
| `docker-compose.override.yml` | Docker integration | Adds ICP addon to HA Docker setup |
| `example_automations.yaml` | Example automations | Sample automations using ICP sensor |

## 🔧 Setup Methods

### Method 1: Direct Configuration (Recommended)

Add the contents of these files to your existing Home Assistant configuration:

1. **Add REST sensor** - Copy content from `icp_rest_sensor.yaml` to your `configuration.yaml`:
   ```yaml
   rest:
     # Paste the REST sensor configuration here
   ```

2. **Add template sensor** - Copy content from `icp_template_sensor.yaml` to your `configuration.yaml`:
   ```yaml
   template:
     # Paste the template sensor configuration here
   ```

3. **Restart Home Assistant**

### Method 2: Using Packages

1. Create a `packages` directory in your Home Assistant config folder
2. Copy `icp_sensors_package.yaml` to `config/packages/`
3. Add to your `configuration.yaml`:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
4. Restart Home Assistant

### Method 3: Include Files

1. Copy `icp_rest_sensor.yaml` and `icp_template_sensor.yaml` to your config directory
2. Add to your `configuration.yaml`:
   ```yaml
   rest: !include icp_rest_sensor.yaml
   template: !include icp_template_sensor.yaml
   ```
3. Restart Home Assistant

## 🐳 Docker Setup

### Add to Existing Docker Compose

If you have an existing Home Assistant Docker setup:

1. Copy `docker-compose.override.yml` to your Home Assistant directory
2. Set your HA token environment variable:
   ```bash
   export HA_TOKEN="your_long_lived_access_token"
   ```
3. Run:
   ```bash
   docker-compose up -d
   ```

### Standalone Docker Setup

Use the main `docker-compose.yml` in the project root for a complete setup with both Home Assistant and the ICP addon.

## 🤖 Example Automations

The `example_automations.yaml` file contains sample automations that demonstrate:

- **Security monitoring**: Alert when mnemonic backup is missing
- **Change tracking**: Log principal ID changes
- **Connection monitoring**: Track addon connection status
- **Backup notifications**: Alert when new backups are created

Copy these to your `automations.yaml` or use them as inspiration for your own automations.

## 📊 Available Sensor Data

The `sensor.icp_identity` entity provides these attributes for automations:

| Attribute | Type | Description |
|-----------|------|-------------|
| `principal` | string | ICP Principal ID |
| `public_key_short` | string | Abbreviated public key |
| `full_public_key` | string | Complete public key |
| `network` | string | Network (mainnet/local) |
| `has_mnemonic` | boolean | Whether mnemonic backup exists |
| `identity_file_exists` | boolean | Whether identity file exists |
| `backup_count` | number | Number of backups |
| `data_size_mb` | number | Data directory size |
| `connection_status` | string | Addon connection status |
| `automation_ready` | boolean | Always true |
| `entity_status` | string | "dynamic" |

## 🔍 Troubleshooting

### Sensor Not Appearing

1. Check Home Assistant logs for configuration errors
2. Verify the ICP addon is running: `docker ps | grep icp-identity`
3. Test the addon API: `curl http://localhost:8099/stats`
4. Restart Home Assistant after configuration changes

### Data Not Updating

1. Check if REST sensor is working: Look for `sensor.icp_addon_status_internal`
2. Verify container networking: Ensure containers can communicate
3. Check scan_interval (default: 30 seconds)

### Container Communication Issues

If using Docker, ensure:
- Containers are on the same network
- Use container name `icp-identity` in REST sensor URL
- Not `localhost` or `127.0.0.1`

## 🆔 Unique ID

The sensor uses unique ID `icp_identity_consolidated_f8e2a9b3` which enables:
- ✅ Dashboard management
- ✅ Automation creation
- ✅ Entity customization
- ✅ UI integration

## 🔄 Dynamic Updates

All sensor data updates automatically every 30 seconds from the addon API. When you:
- Regenerate your ICP identity
- Create backups
- Change networks

The Home Assistant sensor will reflect these changes within 30 seconds.