#!/bin/bash
# Home Assistant ICP Identity Integration Setup Script

set -e

echo "🏠 Home Assistant ICP Identity Integration Setup"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "icp_rest_sensor.yaml" ]; then
    echo "❌ Error: Please run this script from the homeassistant-integration directory"
    exit 1
fi

# Function to detect HA config directory
detect_ha_config() {
    local possible_paths=(
        "/config"
        "~/.homeassistant"
        "/usr/share/hassio/homeassistant"
        "../homeassistant-docker/config"
        "./config"
    )
    
    for path in "${possible_paths[@]}"; do
        expanded_path=$(eval echo "$path")
        if [ -f "$expanded_path/configuration.yaml" ]; then
            echo "$expanded_path"
            return 0
        fi
    done
    
    return 1
}

# Detect Home Assistant config directory
echo "🔍 Detecting Home Assistant configuration directory..."
HA_CONFIG_DIR=$(detect_ha_config)

if [ $? -eq 0 ]; then
    echo "✅ Found Home Assistant config: $HA_CONFIG_DIR"
else
    echo "❓ Couldn't auto-detect Home Assistant config directory."
    read -p "Enter path to your HA config directory: " HA_CONFIG_DIR
fi

# Validate config directory
if [ ! -f "$HA_CONFIG_DIR/configuration.yaml" ]; then
    echo "❌ Error: configuration.yaml not found in $HA_CONFIG_DIR"
    exit 1
fi

echo ""
echo "📋 Available setup methods:"
echo "1. Direct configuration (add to existing configuration.yaml)"
echo "2. Package-based setup (create packages directory)"
echo "3. Include files (use !include statements)"
echo ""

read -p "Choose setup method (1-3): " setup_method

case $setup_method in
    1)
        echo ""
        echo "📝 Direct Configuration Setup"
        echo "----------------------------"
        echo ""
        echo "⚠️  IMPORTANT: You need to manually add the following to your configuration.yaml:"
        echo ""
        echo "🔹 Add this under 'rest:' section:"
        echo ""
        cat icp_rest_sensor.yaml | grep -A 100 "rest:" | tail -n +2
        echo ""
        echo "🔹 Add this under 'template:' section:"
        echo ""
        cat icp_template_sensor.yaml | grep -A 100 "template:" | tail -n +2
        echo ""
        echo "📖 Full examples are available in the README.md file"
        ;;
        
    2)
        echo ""
        echo "📦 Package-based Setup"
        echo "---------------------"
        
        # Create packages directory
        mkdir -p "$HA_CONFIG_DIR/packages"
        
        # Copy package file
        cp icp_sensors_package.yaml "$HA_CONFIG_DIR/packages/"
        echo "✅ Copied package file to $HA_CONFIG_DIR/packages/"
        
        # Check if packages are enabled in configuration.yaml
        if grep -q "packages:" "$HA_CONFIG_DIR/configuration.yaml"; then
            echo "✅ Packages already enabled in configuration.yaml"
        else
            echo ""
            echo "⚠️  You need to add this to your configuration.yaml under 'homeassistant:' section:"
            echo ""
            echo "homeassistant:"
            echo "  packages: !include_dir_named packages"
            echo ""
        fi
        ;;
        
    3)
        echo ""
        echo "📁 Include Files Setup"
        echo "--------------------"
        
        # Copy include files
        cp icp_rest_sensor.yaml "$HA_CONFIG_DIR/"
        cp icp_template_sensor.yaml "$HA_CONFIG_DIR/"
        echo "✅ Copied configuration files to $HA_CONFIG_DIR/"
        
        echo ""
        echo "⚠️  You need to add this to your configuration.yaml:"
        echo ""
        echo "rest: !include icp_rest_sensor.yaml"
        echo "template: !include icp_template_sensor.yaml"
        echo ""
        ;;
        
    *)
        echo "❌ Invalid selection. Exiting."
        exit 1
        ;;
esac

echo ""
echo "🔄 Next Steps:"
echo "1. Restart Home Assistant"
echo "2. Check for the 'sensor.icp_identity' entity"
echo "3. Add it to your dashboard or automations"
echo ""
echo "📖 For examples and troubleshooting, see README.md"
echo "🎉 Setup complete!"