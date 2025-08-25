# Add a custom JS card to a Home Assistant dashboard

## Put the file in www

Place your card at:
```
/config/www/icp_addon/icp-addon-card.js
```

After saving, the file will be served at:
```
http(s)://<ha-host>:8123/local/icp_addon/icp-addon-card.js
```

Tip: if you can open that URL in a browser (you should see the JS), the path is correct.

##Expose it as a Lovelace resource (UI method)

In Home Assistant, go to your Profile and enable Advanced Mode (required to see Resources).

Go to Settings → Dashboards → (⋮) → Resources → + Add resource.
```
URL: /local/icp_addon/icp-addon-card.js?v=1
Resource type: JavaScript Module.
```
Save.

Tip: bump the ?v= number whenever you update the file to bust the browser cache.

YAML alternative (if using YAML mode for Lovelace)
```yaml
lovelace:
  resources:
    - url: /local/icp_addon/icp-addon-card.js?v=1
      type: module
```

Restart Home Assistant after editing configuration.yaml.

## Add the card to a dashboard

Open your dashboard, click Edit → Add card → Manual.

Paste minimal config:
```yaml
type: custom:icp-addon-card
title: ICP Card
api_base: http://127.0.0.1:8099
identity_url: http://127.0.0.1:8099/api/v1/identity
```

where the type it’s the custom element tag name from your JS file, prefixed with custom:

In your card you have:
```javascript
customElements.define("icp-addon-card", IcpAddonCard);
(window.customCards = window.customCards || []).push({ type: "icp-addon-card", ... });
```

So the YAML type is:
``` yaml
type: custom:icp-addon-card
```

## Update/refresh

When you change the JS file, bump the resource URL (?v=2, ?v=3, …) and hard-reload the browser (Ctrl/Cmd+Shift+R).

In the mobile app, pull down to refresh or force-quit and reopen.

## Quick troubleshooting

“Custom element doesn’t exist”: the resource isn’t loaded. Check Settings → Dashboards → Resources and the URL.

Open the browser console:
```javascript
customElements.get('icp-addon-card') 
```
should return a function (not undefined).

Network tab should show 200 for 
```
/local/icp_addon/icp-addon-card.js?v=N.
```
Clear cache if you still see old behavior.