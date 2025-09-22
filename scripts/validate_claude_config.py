import json
import sys
import os

def validate_claude_config():
    """Validate Claude Desktop configuration file"""
    config_path = os.path.expandvars(r'%APPDATA%\Claude\claude_desktop_config.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ JSON is valid!")
        
        if 'mcpServers' in config:
            servers = list(config['mcpServers'].keys())
            print(f"✅ MCP Servers configured: {servers}")
            
            for server_name, server_config in config['mcpServers'].items():
                required_fields = ['command', 'args']
                missing_fields = [field for field in required_fields if field not in server_config]
                
                if missing_fields:
                    print(f"⚠️  {server_name}: Missing required fields: {missing_fields}")
                else:
                    print(f"✅ {server_name}: Configuration looks good")
        else:
            print("⚠️  No mcpServers section found")
            
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if validate_claude_config():
        sys.exit(0)
    else:
        sys.exit(1)